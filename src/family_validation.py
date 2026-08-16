"""Family-isolated B refinement and one-shot C acceptance."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from agent import LocalModelClient
from appworld_runtime import run_task
from contracts import contract_prompt, parse_contract_response
from family_generation import instance_terms
from official_agent import local_model_config
from retrieval_bridge import load_skill_library
from schemas import Candidate, Snapshot
from skill_generation import parse_skill_markdown, refinement_prompt
from utils import canonical_hash, read_json, write_json


def validate_family_shard(
    candidates_root: str | Path,
    split_path: str | Path,
    output_root: str | Path,
    model: LocalModelClient,
    shard_index: int,
    num_shards: int,
    seed: int = 42,
    max_b_attempts: int = 3,
) -> dict[str, Any]:
    candidates_root, output_root = Path(candidates_root), Path(output_root)
    gate = read_json(output_root.parent / "subskill_report.json")
    if not gate.get("count_gate_passed") or gate.get("failed"):
        raise ValueError("candidate count gate has not passed")
    families = read_json(split_path)["families"]
    selected = [family for index, family in enumerate(families) if index % num_shards == shard_index]
    results = [
        validate_family(
            family, candidates_root, output_root, model, seed, max_b_attempts
        )
        for family in selected
    ]
    report = {
        "schema_version": "family_validation_shard_v1",
        "shard_index": shard_index, "num_shards": num_shards,
        "families": len(results),
        "b_passed": sum(item["b_status"] == "passed" for item in results),
        "c_passed": sum(item["c_status"] == "passed" for item in results),
        "rejected": sum(item["status"] == "rejected" for item in results),
        "results": results,
    }
    write_json(output_root / f"shard_{shard_index}.json", report)
    return report


def validate_family(
    family: dict[str, Any],
    candidates_root: Path,
    output_root: Path,
    model: LocalModelClient,
    seed: int,
    max_b_attempts: int,
) -> dict[str, Any]:
    family_id = family["family_id"]
    family_output = output_root / family_id
    final_path = family_output / "result.json"
    if final_path.exists():
        return read_json(final_path)
    bundle_ids = _bundle_ids(candidates_root, family_id)
    if not bundle_ids or not bundle_ids[0].endswith("-core"):
        raise ValueError(f"{family_id}: missing core candidate")
    b_attempts = []
    b_record = None
    for attempt in range(max_b_attempts):
        attempt_path = family_output / f"b_attempt_{attempt}.json"
        if attempt_path.exists():
            b_record = read_json(attempt_path)
        else:
            b_record = _run_bundle(
                family["refinement_task"], family_id, bundle_ids, candidates_root,
                seed, f"skill_build__{family_id}__b__{attempt}",
            )
            write_json(attempt_path, b_record, overwrite=False)
        b_attempts.append({
            "attempt": attempt, "success": b_record["success"], "path": str(attempt_path)
        })
        if b_record["success"]:
            break
        if attempt + 1 < max_b_attempts:
            _refine_core(
                family, candidates_root, family_output, b_record, model, attempt + 1, seed
            )
    if not b_record or not b_record["success"]:
        result = {
            "family_id": family_id, "status": "rejected",
            "b_status": "failed", "c_status": "not_run",
            "bundle_skill_ids": bundle_ids, "b_attempts": b_attempts,
        }
        write_json(final_path, result)
        return result

    c_path = family_output / "c_acceptance.json"
    if c_path.exists():
        c_record = read_json(c_path)
    else:
        c_record = _run_bundle(
            family["acceptance_task"], family_id, bundle_ids, candidates_root,
            seed, f"skill_build__{family_id}__c",
        )
        write_json(c_path, c_record, overwrite=False)
    api_stage = _subskill_stage_evidence(bundle_ids, candidates_root, c_record)
    status = "accepted" if c_record["success"] else "rejected"
    result = {
        "family_id": family_id, "status": status,
        "b_status": "passed", "c_status": "passed" if c_record["success"] else "failed",
        "bundle_skill_ids": bundle_ids, "b_attempts": b_attempts,
        "c_path": str(c_path), "subskill_api_stage_evidence": api_stage,
        "c_feedback_used_for_refinement": False,
    }
    write_json(final_path, result)
    return result


def _bundle_ids(candidates_root: Path, family_id: str) -> list[str]:
    core = f"{family_id}-core"
    shared = []
    required = set(read_json(
        Path("outputs/skill_build/references") / f"{family_id}.json"
    )["required_apis"])
    for metadata_path in candidates_root.glob("shared-*/metadata.json"):
        metadata = read_json(metadata_path)
        if family_id not in metadata.get("supporting_family_ids", []):
            continue
        overlap = len(required & set(metadata.get("supporting_apis", [])))
        shared.append((-overlap, metadata["skill_id"]))
    return [core] + [skill_id for _, skill_id in sorted(shared)[:4]]


def _run_bundle(
    task_id: str,
    family_id: str,
    bundle_ids: list[str],
    candidates_root: Path,
    seed: int,
    experiment_name: str,
) -> dict[str, Any]:
    all_skills = load_skill_library(candidates_root)
    library = {skill_id: all_skills[skill_id] for skill_id in bundle_ids}
    snapshot = Snapshot(
        task_id=task_id,
        query=f"Train family {family_id} deduction validation",
        skills=tuple(Candidate(skill_id, rank, 1.0 / rank)
                     for rank, skill_id in enumerate(bundle_ids, 1)),
        provenance={"source_split": "train", "family_id": family_id},
    )
    return run_task(
        task_id=task_id, split="train", condition="Flat-NoPD", seed=seed,
        experiment_name=experiment_name, snapshot=snapshot, library=library,
        model=local_model_config(
            os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
            os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
        ),
        max_steps=30,
    )


def _refine_core(
    family: dict[str, Any],
    candidates_root: Path,
    family_output: Path,
    failed_record: dict[str, Any],
    model: LocalModelClient,
    revision: int,
    seed: int,
) -> None:
    family_id, skill_id = family["family_id"], f"{family['family_id']}-core"
    directory = candidates_root / skill_id
    skill = load_skill_library(candidates_root)[skill_id]
    revision_root = family_output / "revisions" / f"revision_{revision}"
    raw_path = revision_root / "skill_response.json"
    feedback = {
        "evaluation": failed_record["evaluation"],
        "steps": failed_record["steps"],
        "instruction_is_validation_only": True,
    }
    if raw_path.exists():
        reply_text = str(read_json(raw_path)["response"])
    else:
        reply = model.complete(
            [{"role": "user", "content": refinement_prompt(skill.body, feedback)}],
            seed + revision,
        )
        reply_text = reply.text
        write_json(raw_path, {
            "revision": revision, "seed": seed + revision,
            "response": reply_text, "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
        })
    refined = parse_skill_markdown(skill_id, reply_text, skill.metadata)
    instruction = _task_instruction(family["refinement_task"])
    leaked = sorted(term for term in instance_terms(instruction)
                    if term.casefold() in refined.body.casefold())
    if leaked:
        raise ValueError(f"{family_id}: B refinement leaked instance terms: {leaked[:5]}")
    contract_path = revision_root / "contract_response.json"
    if contract_path.exists():
        contract_text = str(read_json(contract_path)["response"])
    else:
        reply = model.complete(
            [{"role": "user", "content": contract_prompt(skill_id, refined.body)}],
            seed + revision,
        )
        contract_text = reply.text
        write_json(contract_path, {
            "revision": revision, "seed": seed + revision,
            "response": contract_text, "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
        })
    contract = parse_contract_response(contract_text, skill_id)
    previous_body = (directory / "SKILL.md").read_text(encoding="utf-8")
    previous_contract = read_json(directory / "contract.json")
    (revision_root / "previous_SKILL.md").write_text(previous_body, encoding="utf-8")
    write_json(revision_root / "previous_contract.json", previous_contract)
    (directory / "SKILL.md").write_text(refined.body.rstrip() + "\n", encoding="utf-8")
    write_json(directory / "contract.json", contract.to_dict())
    metadata = read_json(directory / "metadata.json")
    metadata.update({
        "validation_status": "b_refining", "version": revision,
        "last_refinement_task": family["refinement_task"],
        "content_hash": canonical_hash(refined.retrieval_record()),
    })
    write_json(directory / "metadata.json", metadata)


def _subskill_stage_evidence(
    bundle_ids: list[str], candidates_root: Path, record: dict[str, Any]
) -> dict[str, Any]:
    code = "\n".join(str(step.get("code", "")) for step in record.get("steps", []))
    evidence = {}
    for skill_id in bundle_ids:
        if not skill_id.startswith("shared-"):
            continue
        metadata = read_json(candidates_root / skill_id / "metadata.json")
        matched = [
            api for api in metadata.get("supporting_apis", [])
            if api in code or f"apis.{api}" in code
        ]
        evidence[skill_id] = {
            "supporting_apis_observed": matched,
            "stage_observed": bool(matched),
            "agent_reported_used": skill_id in record.get("used_skill_ids", []),
        }
    return evidence


def finalize_validated_library(
    candidates_root: str | Path,
    library_root: str | Path,
    validation_root: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    candidates_root, library_root, validation_root = (
        Path(candidates_root), Path(library_root), Path(validation_root)
    )
    results = [
        read_json(path) for path in sorted(validation_root.glob("*/result.json"))
    ]
    if len(results) != 30:
        raise ValueError(f"expected 30 family results, found {len(results)}")
    accepted_families = {
        result["family_id"] for result in results if result["c_status"] == "passed"
    }
    promoted, rejected = [], []
    for directory in sorted(p for p in candidates_root.iterdir() if p.is_dir()):
        metadata = read_json(directory / "metadata.json")
        skill_id = directory.name
        if metadata["candidate_type"] == "core":
            eligible = metadata["family_id"] in accepted_families
            evidence_families = [metadata["family_id"]] if eligible else []
        else:
            evidence_families = []
            for result in results:
                stage = result.get("subskill_api_stage_evidence", {}).get(skill_id, {})
                if result["c_status"] == "passed" and stage.get("stage_observed"):
                    evidence_families.append(result["family_id"])
            eligible = len(set(evidence_families)) >= 2
        metadata.update({
            "validation_status": "accepted" if eligible else "rejected",
            "c_evidence_families": sorted(set(evidence_families)),
            "validation_scope": (
                "family-level C acceptance" if metadata["candidate_type"] == "core"
                else "bundle-associated API-stage evidence; not causal attribution"
            ),
        })
        write_json(directory / "metadata.json", metadata)
        if eligible:
            destination = library_root / skill_id
            if destination.exists():
                if read_json(destination / "metadata.json").get("content_hash") != metadata.get("content_hash"):
                    raise FileExistsError(f"library conflict: {destination}")
            else:
                shutil.copytree(directory, destination)
            promoted.append(skill_id)
        else:
            rejected.append(skill_id)
    report = {
        "schema_version": "validated_library_report_v1",
        "families": len(results), "accepted_families": len(accepted_families),
        "promoted": promoted, "rejected": rejected,
        "library_size": len(promoted),
        "c_feedback_used_for_refinement": False,
    }
    write_json(output_path, report)
    return report


def assert_frozen_library_ready(root: str | Path) -> dict[str, int]:
    directories = [
        path for path in Path(root).iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    ]
    invalid = []
    for directory in directories:
        metadata = read_json(directory / "metadata.json")
        if (
            metadata.get("source_split") != "train"
            or metadata.get("validation_status") != "accepted"
        ):
            invalid.append(directory.name)
    if invalid:
        raise ValueError(f"library contains non-accepted skills: {invalid[:20]}")
    if not directories:
        raise ValueError("skill library is empty")
    return {"skills": len(directories), "validated": len(directories)}


def _task_instruction(task_id: str) -> str:
    root = Path(os.environ.get("APPWORLD_ROOT", "data/appworld"))
    return json.loads(
        (root / "data" / "tasks" / task_id / "specs.json").read_text(encoding="utf-8")
    )["instruction"]
