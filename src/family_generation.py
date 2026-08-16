"""Train-only, resumable family candidate generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent import LocalModelClient
from contracts import contract_from_mapping
from schemas import Contract, Skill
from skill_generation import parse_skill_markdown
from utils import canonical_hash, read_json, write_json


MODEL_ID = "Qwen/Qwen3-Coder-30B-A3B-Instruct"
PROMPT_VERSION = "family_candidate_v1"
QUOTED = re.compile(r'["“”]([^"“”]{4,})["“”]')
CAPITALIZED_PHRASE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
NUMBER = re.compile(r"(?<![A-Za-z])\d{2,}(?![A-Za-z])")
GENERIC_TERMS = frozenset({"Title", "Artists", "Simple Note", "File System"})


def candidate_prompt(reference: dict[str, Any]) -> str:
    evidence = {
        key: reference[key] for key in (
            "ground_truth_plan", "ground_truth_api_calls",
            "successful_trajectory_steps", "required_apps", "required_apis",
        )
    }
    return """Distill reusable procedural skills for an AppWorld agent.
Create exactly one core skill. Optionally create at most one reusable_subskill only when it is
independently useful across task families and has a clear input/output boundary.

Never copy instance names, IDs, emails, dates, numbers, answers, or task wording. Generalize
the workflow. Every skill_markdown is a complete SKILL.md with YAML name and description,
then: When to Use, Preconditions, Procedure, Relevant APIs / Tools, Failure Handling,
Verification.

Return JSON only:
{"skills":[{"type":"core","skill_markdown":"...","contract":{
"capability":"...","domain":"...","apps":[],"inputs":[],"outputs":[],
"preconditions":[],"effects":[],"api_patterns":[],"failure_modes":[]}}]}
The list has exactly one core and zero or one reusable_subskill.

Sanitized evidence (argument values removed):
""" + json.dumps(evidence, ensure_ascii=False, indent=2)


def parse_candidate_response(
    family_id: str, text: str, instruction: str
) -> list[tuple[str, Skill, Contract]]:
    payload = _json_object(text)
    records = payload.get("skills")
    if not isinstance(records, list) or not 1 <= len(records) <= 2:
        raise ValueError("response must contain one or two skills")
    if not all(isinstance(item, dict) for item in records):
        raise ValueError("each skill must be an object")
    kinds = [item.get("type") for item in records]
    if kinds.count("core") != 1 or kinds.count("reusable_subskill") > 1:
        raise ValueError("exactly one core and at most one reusable_subskill required")
    if any(kind not in {"core", "reusable_subskill"} for kind in kinds):
        raise ValueError("unknown candidate type")

    forbidden = instance_terms(instruction)
    parsed = []
    for record in records:
        kind = record["type"]
        skill_id = f"{family_id}-{'core' if kind == 'core' else 'subskill'}"
        markdown, mapping = record.get("skill_markdown"), record.get("contract")
        if not isinstance(markdown, str) or not isinstance(mapping, dict):
            raise ValueError("candidate needs skill_markdown and contract")
        leaked = sorted(term for term in forbidden if term.casefold() in markdown.casefold())
        if leaked:
            raise ValueError(f"candidate contains task-instance terms: {leaked[:5]}")
        skill = parse_skill_markdown(
            skill_id, markdown, {"family_id": family_id, "candidate_type": kind}
        )
        contract = contract_from_mapping({**mapping, "skill_id": skill_id})
        parsed.append((kind, skill, contract))
    return parsed


def generate_family_candidates(
    split_path: str | Path,
    references_root: str | Path,
    candidates_root: str | Path,
    output_root: str | Path,
    model: LocalModelClient,
    seeds: tuple[int, ...] = (42, 43, 44),
) -> dict[str, Any]:
    split = read_json(split_path)
    output_root, candidates_root = Path(output_root), Path(candidates_root)
    results = []
    for family in split["families"]:
        family_id = family["family_id"]
        family_output = output_root / "generation" / family_id
        complete_path = family_output / "complete.json"
        if complete_path.exists():
            done = read_json(complete_path)
            if all((candidates_root / sid / "SKILL.md").exists() for sid in done["skill_ids"]):
                results.append({"family_id": family_id, "status": "skipped_complete",
                                "skill_ids": done["skill_ids"]})
                continue
        reference = read_json(Path(references_root) / f"{family_id}.json")
        results.append(_generate_one(
            family, reference, candidates_root, family_output, model, seeds
        ))
    report = {
        "schema_version": "family_generation_report_v1",
        "prompt_version": PROMPT_VERSION,
        "model_id": model.model_id,
        "families": len(results),
        "completed": sum(r["status"] != "failed" for r in results),
        "failed": sum(r["status"] == "failed" for r in results),
        "candidate_count": sum(len(r.get("skill_ids", [])) for r in results),
        "results": results,
    }
    write_json(output_root / "generation_report.json", report)
    return report


def _generate_one(
    family: dict[str, Any],
    reference: dict[str, Any],
    candidates_root: Path,
    output: Path,
    model: LocalModelClient,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    family_id, prompt = family["family_id"], candidate_prompt(reference)
    errors = []
    for attempt, seed in enumerate(seeds, 1):
        raw_path = output / f"raw_attempt_{attempt}.json"
        if raw_path.exists():
            response = str(read_json(raw_path)["response"])
        else:
            reply = model.complete([{"role": "user", "content": prompt}], seed)
            response = reply.text
            write_json(raw_path, {
                "family_id": family_id, "seed": seed, "model_id": model.model_id,
                "prompt_hash": canonical_hash(prompt), "response": response,
                "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
            })
        try:
            candidates = parse_candidate_response(
                family_id, response, reference["instruction"]
            )
            for kind, skill, contract in candidates:
                _write_package(
                    candidates_root, family, reference, kind, skill, contract,
                    seed, prompt, raw_path,
                )
            skill_ids = [skill.skill_id for _, skill, _ in candidates]
            write_json(output / "complete.json", {
                "family_id": family_id, "skill_ids": skill_ids, "seed": seed,
                "reference_hash": canonical_hash(reference),
                "prompt_hash": canonical_hash(prompt),
            })
            stale_error = output / "error.json"
            if stale_error.exists():
                stale_error.unlink()
            return {"family_id": family_id, "status": "generated", "skill_ids": skill_ids}
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
    failure = {"family_id": family_id, "status": "failed", "errors": errors}
    write_json(output / "error.json", failure)
    return failure


def _write_package(
    root: Path, family: dict[str, Any], reference: dict[str, Any], kind: str,
    skill: Skill, contract: Contract, seed: int, prompt: str, raw_path: Path,
) -> None:
    destination = root / skill.skill_id
    content_hash = canonical_hash(skill.retrieval_record())
    if destination.exists() and any(destination.iterdir()):
        existing = read_json(destination / "metadata.json")
        if existing.get("content_hash") == content_hash:
            return
        raise FileExistsError(f"refusing to overwrite candidate: {destination}")
    refs = destination / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (destination / "SKILL.md").write_text(skill.body.rstrip() + "\n", encoding="utf-8")
    write_json(destination / "contract.json", contract.to_dict(), overwrite=False)
    write_json(destination / "metadata.json", {
        "skill_id": skill.skill_id, "status": "candidate", "source_split": "train",
        "family_id": family["family_id"], "candidate_type": kind,
        "generation_task": family["generation_task"],
        "refinement_task": family["refinement_task"],
        "acceptance_task": family["acceptance_task"],
        "model_id": MODEL_ID, "generation_seed": seed,
        "prompt_version": PROMPT_VERSION, "prompt_hash": canonical_hash(prompt),
        "reference_hash": canonical_hash(reference), "content_hash": content_hash,
    }, overwrite=False)
    write_json(refs / "api_patterns.json", {
        "required_apis": reference["required_apis"],
        "ground_truth_api_calls": reference["ground_truth_api_calls"],
        "successful_trajectory_steps": reference["successful_trajectory_steps"],
        "contract_api_patterns": list(contract.api_patterns),
    }, overwrite=False)
    write_json(refs / "examples.json", {
        "family_id": family["family_id"], "source_task": reference["task_id"],
        "instruction": reference["instruction"],
    }, overwrite=False)
    write_json(refs / "evidence.json", {
        "split_roles": family, "reference_provenance": reference["provenance"],
        "reference_hash": canonical_hash(reference), "raw_response_path": str(raw_path),
        "raw_response_hash": canonical_hash(raw_path.read_text(encoding="utf-8")),
        "evidence_scope": "generation evidence; not causal validation evidence",
    }, overwrite=False)


def instance_terms(instruction: str) -> set[str]:
    terms = set(QUOTED.findall(instruction))
    terms.update(CAPITALIZED_PHRASE.findall(instruction))
    terms.update(NUMBER.findall(instruction))
    return {
        term.strip() for term in terms
        if len(term.strip()) >= 2 and term.strip() not in GENERIC_TERMS
    }


def _json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("~~~"):
        stripped = re.sub(r"^~~~(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*~~~$", "", stripped)
    # Also accept ordinary Markdown fences without embedding them in the generation prompt.
    if stripped.startswith(chr(96) * 3):
        stripped = stripped.split("\n", 1)[1].rsplit(chr(96) * 3, 1)[0]
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("response contains no JSON object")
    value = json.loads(stripped[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("response JSON must be an object")
    return value
