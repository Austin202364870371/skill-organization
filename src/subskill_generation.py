"""Corpus-level reusable subskill mining from validated Train-only evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent import LocalModelClient
from contracts import contract_from_mapping
from family_generation import _json_object, instance_terms
from skill_generation import parse_skill_markdown
from utils import canonical_hash, read_json, write_json


PROPOSAL_PROMPT_VERSION = "shared_subskill_proposals_v1"
GENERATION_PROMPT_VERSION = "shared_subskill_generation_v1"


def mine_shared_subskills(
    candidates_root: str | Path,
    references_root: str | Path,
    output_root: str | Path,
    model: LocalModelClient,
    min_total: int = 40,
    max_total: int = 60,
    seeds: tuple[int, ...] = (42, 43, 44),
) -> dict[str, Any]:
    candidates_root, references_root, output_root = (
        Path(candidates_root), Path(references_root), Path(output_root)
    )
    cores = _load_cores(candidates_root, references_root)
    proposals = _load_or_propose(cores, output_root, model, seeds)
    results = []
    for proposal in proposals:
        results.append(_generate_subskill(
            proposal, cores, candidates_root, output_root, model, seeds
        ))
    total = len(list(candidates_root.glob("*/SKILL.md")))
    report = {
        "schema_version": "shared_subskill_report_v1",
        "proposal_prompt_version": PROPOSAL_PROMPT_VERSION,
        "generation_prompt_version": GENERATION_PROMPT_VERSION,
        "core_count": len(cores),
        "proposed": len(proposals),
        "generated": sum(item["status"] in {"generated", "skipped_complete"} for item in results),
        "failed": sum(item["status"] == "failed" for item in results),
        "candidate_total": total,
        "minimum_required": min_total,
        "maximum_allowed": max_total,
        "count_gate_passed": min_total <= total <= max_total,
        "results": results,
    }
    write_json(output_root / "subskill_report.json", report)
    return report


def _load_cores(candidates_root: Path, references_root: Path) -> dict[str, dict[str, Any]]:
    records = {}
    for directory in sorted(candidates_root.glob("*-core")):
        metadata = read_json(directory / "metadata.json")
        family_id = metadata["family_id"]
        reference = read_json(references_root / f"{family_id}.json")
        records[directory.name] = {
            "skill_id": directory.name,
            "family_id": family_id,
            "body": (directory / "SKILL.md").read_text(encoding="utf-8"),
            "contract": read_json(directory / "contract.json"),
            "metadata": metadata,
            "reference": reference,
        }
    if len(records) != 30:
        raise ValueError(f"expected 30 core candidates, found {len(records)}")
    return records


def _load_or_propose(
    cores: dict[str, dict[str, Any]],
    output_root: Path,
    model: LocalModelClient,
    seeds: tuple[int, ...],
) -> list[dict[str, Any]]:
    compact = [{
        "skill_id": item["skill_id"],
        "name": _frontmatter_value(item["body"], "name"),
        "description": _frontmatter_value(item["body"], "description"),
        "apps": item["contract"]["apps"],
        "inputs": item["contract"]["inputs"],
        "outputs": item["contract"]["outputs"],
        "api_patterns": item["contract"]["api_patterns"],
        "required_apis": item["reference"]["required_apis"],
    } for item in cores.values()]
    prompt = _proposal_prompt(compact)
    prompt_hash = canonical_hash(prompt)
    proposal_root = output_root / "subskill_generation" / "_proposals"
    errors = []
    for attempt, seed in enumerate(seeds, 1):
        raw_path = proposal_root / f"raw_attempt_{attempt}.json"
        if raw_path.exists():
            cached = read_json(raw_path)
            if cached.get("prompt_hash") != prompt_hash:
                raise ValueError(f"proposal cache prompt hash mismatch: {raw_path}")
            response = str(cached["response"])
        else:
            reply = model.complete([{"role": "user", "content": prompt}], seed)
            response = reply.text
            write_json(raw_path, {
                "seed": seed, "model_id": model.model_id,
                "prompt_version": PROPOSAL_PROMPT_VERSION,
                "prompt_hash": prompt_hash, "response": response,
                "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
            })
        try:
            proposals = _parse_proposals(response, cores)
            write_json(proposal_root / "complete.json", {
                "proposal_count": len(proposals),
                "proposal_hash": canonical_hash(proposals),
                "prompt_hash": prompt_hash,
                "proposals": proposals,
            })
            stale = proposal_root / "error.json"
            if stale.exists():
                stale.unlink()
            return proposals
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
    write_json(proposal_root / "error.json", {"errors": errors})
    raise ValueError(f"subskill proposal generation failed: {errors}")


def _proposal_prompt(compact: list[dict[str, Any]]) -> str:
    return """Identify 10 to 15 genuinely reusable procedural subskills shared by this
Train-only AppWorld core-skill corpus. A proposal is valid only if:
- at least three distinct core skills need the procedure;
- it has a clear input/output boundary;
- it is independently useful, not a restatement of a full task;
- it is more substantive than login alone;
- its APIs are supported by the supplied records.

Return JSON only:
{"proposals":[{"capability":"concise unique name","description":"...",
"supporting_core_ids":["id1","id2","id3"],"supporting_apis":["app.method"],
"inputs":["..."],"outputs":["..."]}]}

Do not invent support IDs or APIs. Prefer pagination, entity resolution, cross-app joins,
set aggregation, temporal filtering, safe batch mutation, ranking, and verification when
the evidence supports them. Do not force near-duplicates.

CORPUS:
""" + json.dumps(compact, ensure_ascii=False, indent=2)


def _parse_proposals(text: str, cores: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    values = _json_object(text).get("proposals")
    if not isinstance(values, list) or not 10 <= len(values) <= 15:
        raise ValueError("proposal response must contain 10 to 15 entries")
    known_ids = set(cores)
    result, capabilities = [], set()
    for value in values:
        if not isinstance(value, dict):
            raise ValueError("proposal must be an object")
        capability = str(value.get("capability", "")).strip()
        description = str(value.get("description", "")).strip()
        support_ids = list(dict.fromkeys(value.get("supporting_core_ids", [])))
        requested_apis = list(dict.fromkeys(value.get("supporting_apis", [])))
        inputs, outputs = value.get("inputs"), value.get("outputs")
        if not capability or not description:
            raise ValueError("proposal needs capability and description")
        key = re.sub(r"\W+", " ", capability.casefold()).strip()
        if key in capabilities:
            raise ValueError(f"duplicate proposal capability: {capability}")
        capabilities.add(key)
        if len(support_ids) < 3 or not set(support_ids) <= known_ids:
            raise ValueError(f"{capability}: requires at least three known supporting cores")
        supported_apis = {
            api for skill_id in support_ids
            for api in cores[skill_id]["reference"]["required_apis"]
        }
        # Reference trajectories, rather than model wording, are authoritative.
        supporting_apis = [api for api in requested_apis if api in supported_apis]
        rejected_apis = [api for api in requested_apis if api not in supported_apis]
        if not supporting_apis:
            raise ValueError(f"{capability}: no supporting API comes from references")
        if not isinstance(inputs, list) or not inputs or not all(isinstance(x, str) and x.strip() for x in inputs):
            raise ValueError(f"{capability}: non-empty inputs required")
        if not isinstance(outputs, list) or not outputs or not all(isinstance(x, str) and x.strip() for x in outputs):
            raise ValueError(f"{capability}: non-empty outputs required")
        proposal = {
            "capability": capability, "description": description,
            "supporting_core_ids": support_ids, "supporting_apis": supporting_apis,
            "inputs": inputs, "outputs": outputs,
        }
        proposal["proposal_id"] = _proposal_id(proposal)
        if rejected_apis:
            proposal["rejected_supporting_apis"] = rejected_apis
        result.append(proposal)
    return result


def _generate_subskill(
    proposal: dict[str, Any],
    cores: dict[str, dict[str, Any]],
    candidates_root: Path,
    output_root: Path,
    model: LocalModelClient,
    seeds: tuple[int, ...],
) -> dict[str, Any]:
    skill_id = proposal["proposal_id"]
    output = output_root / "subskill_generation" / skill_id
    destination = candidates_root / skill_id
    complete_path = output / "complete.json"
    if complete_path.exists() and (destination / "SKILL.md").exists():
        return {"skill_id": skill_id, "status": "skipped_complete"}
    prompt = _generation_prompt(proposal, cores)
    errors = []
    for attempt, seed in enumerate(seeds, 1):
        raw_path = output / f"raw_attempt_{attempt}.json"
        if raw_path.exists():
            response = str(read_json(raw_path)["response"])
        else:
            reply = model.complete([{"role": "user", "content": prompt}], seed)
            response = reply.text
            write_json(raw_path, {
                "skill_id": skill_id, "seed": seed, "model_id": model.model_id,
                "prompt_hash": canonical_hash(prompt), "response": response,
                "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
            })
        try:
            skill, contract = _parse_subskill(response, skill_id, proposal, cores)
            _write_subskill_package(
                destination, skill, contract, proposal, cores, seed, prompt, raw_path
            )
            write_json(complete_path, {
                "skill_id": skill_id, "seed": seed,
                "content_hash": canonical_hash(skill.retrieval_record()),
                "proposal_hash": canonical_hash(proposal),
            })
            stale = output / "error.json"
            if stale.exists():
                stale.unlink()
            return {"skill_id": skill_id, "status": "generated"}
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
    write_json(output / "error.json", {"skill_id": skill_id, "errors": errors})
    return {"skill_id": skill_id, "status": "failed", "errors": errors}


def _generation_prompt(proposal: dict[str, Any], cores: dict[str, dict[str, Any]]) -> str:
    proposal_for_generation = {
        key: value for key, value in proposal.items()
        if key != "rejected_supporting_apis"
    }
    evidence = [{
        "skill_id": sid,
        "skill_markdown": cores[sid]["body"],
        "required_apis": cores[sid]["reference"]["required_apis"],
    } for sid in proposal["supporting_core_ids"][:5]]
    return """Write one concise reusable AppWorld subskill from the supplied proposal and
Train-only evidence. It must be independently callable, have explicit inputs and outputs,
cover only the shared procedure, avoid task-instance values, and include concrete failure
handling and verification.

Return JSON only:
{"skill_markdown":"complete SKILL.md","contract":{"capability":"...","domain":"...",
"apps":[],"inputs":[],"outputs":[],"preconditions":[],"effects":[],
"api_patterns":[],"failure_modes":[]}}

SKILL.md must use YAML frontmatter with name and description, followed by: When to Use,
Preconditions, Procedure, Relevant APIs / Tools, Failure Handling, Verification.
Do not broaden beyond the proposal or invent APIs.

PROPOSAL:
""" + json.dumps(proposal_for_generation, ensure_ascii=False, indent=2) + "\nEVIDENCE:\n" + json.dumps(
        evidence, ensure_ascii=False, indent=2
    )


def _parse_subskill(
    text: str, skill_id: str, proposal: dict[str, Any], cores: dict[str, dict[str, Any]]
):
    value = _json_object(text)
    markdown, mapping = value.get("skill_markdown"), value.get("contract")
    if not isinstance(markdown, str) or not isinstance(mapping, dict):
        raise ValueError("subskill response needs skill_markdown and contract")
    forbidden = set()
    for sid in proposal["supporting_core_ids"]:
        forbidden.update(instance_terms(cores[sid]["reference"]["instruction"]))
    leaked = sorted(term for term in forbidden if term.casefold() in markdown.casefold())
    if leaked:
        raise ValueError(f"subskill contains task-instance terms: {leaked[:5]}")
    skill = parse_skill_markdown(skill_id, markdown, {
        "candidate_type": "reusable_subskill",
        "supporting_core_ids": proposal["supporting_core_ids"],
    })
    normalized_mapping = _normalize_subskill_contract_mapping(mapping)
    contract = contract_from_mapping({**normalized_mapping, "skill_id": skill_id})
    if not contract.inputs or not contract.outputs or not contract.api_patterns:
        raise ValueError("subskill contract requires inputs, outputs, and api_patterns")
    return skill, contract


def _normalize_subskill_contract_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Losslessly encode structured list items for the strict Contract schema."""
    normalized = dict(mapping)
    for field in (
        "apps", "inputs", "outputs", "preconditions", "effects",
        "api_patterns", "failure_modes",
    ):
        items = mapping.get(field, [])
        if not isinstance(items, list):
            continue
        normalized[field] = [
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if isinstance(item, dict) else item
            for item in items
        ]
    return normalized


def _write_subskill_package(
    destination: Path, skill, contract, proposal: dict[str, Any],
    cores: dict[str, dict[str, Any]], seed: int, prompt: str, raw_path: Path,
) -> None:
    content_hash = canonical_hash(skill.retrieval_record())
    if destination.exists() and any(destination.iterdir()):
        if read_json(destination / "metadata.json").get("content_hash") == content_hash:
            return
        raise FileExistsError(f"refusing to overwrite subskill: {destination}")
    refs = destination / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (destination / "SKILL.md").write_text(skill.body.rstrip() + "\n", encoding="utf-8")
    write_json(destination / "contract.json", contract.to_dict(), overwrite=False)
    family_ids = sorted({cores[sid]["family_id"] for sid in proposal["supporting_core_ids"]})
    write_json(destination / "metadata.json", {
        "skill_id": skill.skill_id, "status": "candidate", "source_split": "train",
        "candidate_type": "reusable_subskill", "supporting_core_ids": proposal["supporting_core_ids"],
        "supporting_family_ids": family_ids, "supporting_apis": proposal["supporting_apis"],
        "model_id": "Qwen/Qwen3-Coder-30B-A3B-Instruct", "generation_seed": seed,
        "prompt_version": GENERATION_PROMPT_VERSION, "prompt_hash": canonical_hash(prompt),
        "contract_normalization": "structured_items_to_canonical_json_v1",
        "proposal_hash": canonical_hash(proposal), "content_hash": content_hash,
    }, overwrite=False)
    write_json(refs / "api_patterns.json", {
        "supporting_apis": proposal["supporting_apis"],
        "contract_api_patterns": list(contract.api_patterns),
    }, overwrite=False)
    write_json(refs / "examples.json", {
        "supporting_core_ids": proposal["supporting_core_ids"],
        "supporting_family_ids": family_ids,
    }, overwrite=False)
    write_json(refs / "evidence.json", {
        "proposal": proposal,
        "source_reference_hashes": {
            sid: canonical_hash(cores[sid]["reference"])
            for sid in proposal["supporting_core_ids"]
        },
        "raw_response_path": str(raw_path),
        "raw_response_hash": canonical_hash(raw_path.read_text(encoding="utf-8")),
        "evidence_scope": "cross-family Train evidence; execution validation pending",
    }, overwrite=False)


def _proposal_id(proposal: dict[str, Any]) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", proposal["capability"].casefold()).strip("-")[:42]
    return f"shared-{slug}-{canonical_hash(proposal)[:6]}"


def _frontmatter_value(body: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+?)$", body, re.MULTILINE)
    return match.group(1).strip().strip("\"'") if match else ""
