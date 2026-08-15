"""Outcome-first Train-only deduction validation with bounded refinement."""

from __future__ import annotations
import os

from pathlib import Path
from typing import Any

from agent import LocalModelClient
from appworld_runtime import run_task
from official_agent import local_model_config
from contracts import contract_prompt, parse_contract_response
from retrieval_bridge import load_skill_library
from schemas import Candidate, Snapshot
from skill_generation import parse_skill_markdown, refinement_prompt
from utils import canonical_hash, read_json, require_generation_split, write_json


def validate_and_refine(
    skill_directory: str | Path,
    model: LocalModelClient,
    output_directory: str | Path,
    max_rounds: int = 3,
    seed: int = 42,
) -> dict[str, Any]:
    directory = Path(skill_directory)
    metadata_path = directory / "metadata.json"
    metadata = read_json(metadata_path)
    split = str(metadata.get("source_split", ""))
    require_generation_split(split)
    task_id = metadata.get("source_task")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("skill metadata requires source_task")
    output_directory = Path(output_directory)
    attempts = []

    for round_index in range(max_rounds):
        library = load_skill_library(directory.parent)
        skill = library[directory.name]
        snapshot = Snapshot(task_id, "Train deduction validation", (Candidate(skill.skill_id, 1, 1.0),))
        record = run_task(
            task_id=task_id, split="train", condition="Flat-NoPD", seed=seed,
            experiment_name=f"skill_validation__{skill.skill_id}__round_{round_index}",
            snapshot=snapshot, library={skill.skill_id: skill}, model=local_model_config(os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"), os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct")),
        )
        attempt_path = output_directory / skill.skill_id / f"round_{round_index}.json"
        write_json(attempt_path, record, overwrite=False)
        attempts.append({"round": round_index, "success": record["success"], "path": str(attempt_path)})
        if record["success"]:
            metadata.update({
                "validation_status": "validated", "validation_round": round_index,
                "validation_seed": seed, "content_hash": canonical_hash(skill.retrieval_record()),
            })
            write_json(metadata_path, metadata)
            return {"skill_id": skill.skill_id, "status": "validated", "attempts": attempts}
        if round_index + 1 >= max_rounds:
            break

        feedback = {"evaluation": record["evaluation"], "steps": record["steps"]}
        reply = model.complete(
            [{"role": "user", "content": refinement_prompt(skill.body, feedback)}],
            seed + round_index + 1,
        )
        refined = parse_skill_markdown(skill.skill_id, reply.text, skill.metadata)
        (directory / "SKILL.md").write_text(refined.body.rstrip() + "\n", encoding="utf-8")
        contract_reply = model.complete(
            [{"role": "user", "content": contract_prompt(skill.skill_id, refined.body)}],
            seed + round_index + 1,
        )
        contract = parse_contract_response(contract_reply.text, skill.skill_id)
        write_json(directory / "contract.json", contract.to_dict())
        metadata["version"] = round_index + 1
        metadata["validation_status"] = "refining"
        write_json(metadata_path, metadata)

    metadata.update({"validation_status": "rejected", "validation_seed": seed})
    write_json(metadata_path, metadata)
    return {"skill_id": directory.name, "status": "rejected", "attempts": attempts}


def assert_frozen_library_ready(root: str | Path) -> dict[str, int]:
    directories = [path for path in Path(root).iterdir() if path.is_dir() and (path / "SKILL.md").exists()]
    invalid = []
    for directory in directories:
        metadata = read_json(directory / "metadata.json")
        if metadata.get("source_split") != "train" or metadata.get("validation_status") != "validated":
            invalid.append(directory.name)
    if invalid:
        raise ValueError(f"library contains non-validated skills: {invalid[:20]}")
    if not directories:
        raise ValueError("skill library is empty")
    return {"skills": len(directories), "validated": len(directories)}

