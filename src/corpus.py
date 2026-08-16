"""Train-only family splitting and sanitized reference construction."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from utils import canonical_hash, file_hash, write_json


def build_family_split(train_task_ids: list[str]) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    for task_id in train_task_ids:
        family_id, separator, variant = task_id.rpartition("_")
        if not separator or not variant.isdigit():
            raise ValueError(f"invalid AppWorld task id: {task_id}")
        groups.setdefault(family_id, []).append(task_id)
    if len(groups) != 30 or len(train_task_ids) != 90:
        raise ValueError(
            f"expected 30 families and 90 Train tasks, got {len(groups)} and {len(train_task_ids)}"
        )
    families = []
    for family_id, task_ids in sorted(groups.items()):
        ordered = sorted(task_ids, key=lambda value: int(value.rsplit("_", 1)[1]))
        if len(ordered) != 3 or len(set(ordered)) != 3:
            raise ValueError(f"Train family {family_id} must contain exactly three variants")
        families.append({
            "family_id": family_id,
            "generation_task": ordered[0],
            "refinement_task": ordered[1],
            "acceptance_task": ordered[2],
        })
    payload = {"schema_version": "family_split_v1", "families": families}
    payload["split_hash"] = canonical_hash(payload)
    return payload


def prepare_skill_corpus(appworld_root: str | Path, output_root: str | Path) -> dict[str, Any]:
    appworld_root = Path(appworld_root).resolve()
    output_root = Path(output_root)
    dataset_root = appworld_root / "data" / "datasets"
    train_ids = _read_task_ids(dataset_root / "train.txt")
    forbidden_ids = set(_read_task_ids(dataset_root / "dev.txt"))
    forbidden_ids.update(_read_task_ids(dataset_root / "test_normal.txt"))
    forbidden_ids.update(_read_task_ids(dataset_root / "test_challenge.txt"))
    if set(train_ids) & forbidden_ids:
        raise ValueError("Train IDs overlap Dev/Test")
    split = build_family_split(train_ids)
    write_json(output_root / "family_split.json", split)
    references = []
    for family in split["families"]:
        reference = build_family_reference(
            appworld_root, family["family_id"], family["generation_task"]
        )
        write_json(output_root / "references" / f"{family['family_id']}.json", reference)
        references.append(reference)
    report = {
        "schema_version": "skill_corpus_report_v1",
        "train_tasks": len(train_ids),
        "families": len(split["families"]),
        "references": len(references),
        "split_hash": split["split_hash"],
        "reference_hash": canonical_hash(references),
        "dev_test_tasks_read": 0,
    }
    write_json(output_root / "prepare_report.json", report)
    return report


def build_family_reference(
    appworld_root: str | Path, family_id: str, task_id: str
) -> dict[str, Any]:
    task_root = Path(appworld_root) / "data" / "tasks" / task_id
    specs = json.loads((task_root / "specs.json").read_text(encoding="utf-8"))
    ground_truth = task_root / "ground_truth"
    solution_path = ground_truth / "solution.py"
    api_calls_path = ground_truth / "api_calls.json"
    solution = solution_path.read_text(encoding="utf-8")
    plan = [
        line.lstrip()[2:].strip()
        for line in solution.splitlines()
        if line.lstrip().startswith("# ") and "Canary String" not in line
    ]
    api_calls = json.loads(api_calls_path.read_text(encoding="utf-8"))
    required_apps = json.loads((ground_truth / "required_apps.json").read_text(encoding="utf-8"))
    required_apis = json.loads((ground_truth / "required_apis.json").read_text(encoding="utf-8"))
    verification_path = (
        appworld_root / "experiments" / "outputs" / "verification" /
        "tasks" / task_id / "logs" / "api_calls.jsonl"
    )
    successful_steps = []
    if verification_path.exists():
        successful_steps = _sanitize_api_calls(_read_jsonl(verification_path))
    return {
        "schema_version": "family_reference_v1",
        "family_id": family_id,
        "task_id": task_id,
        "instruction": specs["instruction"],
        "ground_truth_plan": plan,
        "ground_truth_api_calls": _sanitize_api_calls(api_calls),
        "successful_trajectory_steps": successful_steps,
        "trajectory_status": "success" if successful_steps else "not_available",
        "failure_evidence": [],
        "required_apps": required_apps,
        "required_apis": required_apis,
        "provenance": {
            "solution_hash": file_hash(solution_path),
            "api_calls_hash": file_hash(api_calls_path),
            "verification_hash": file_hash(verification_path) if verification_path.exists() else None,
        },
    }


def _sanitize_api_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized, seen = [], set()
    for call in calls:
        item = {
            "method": str(call.get("method", "")).upper(),
            "path": _sanitize_path(str(call.get("url", ""))),
            "parameter_names": sorted((call.get("data") or {}).keys()),
        }
        key = (item["method"], item["path"], tuple(item["parameter_names"]))
        if key not in seen:
            seen.add(key)
            sanitized.append(item)
    return sanitized


def _sanitize_path(url: str) -> str:
    path = url.split("?", 1)[0]
    segments = []
    for segment in path.split("/"):
        if segment.isdigit():
            segments.append("{id}")
        elif re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", segment
        ):
            segments.append("{uuid}")
        elif re.fullmatch(r"[0-9a-fA-F]{16,}", segment):
            segments.append("{opaque_id}")
        else:
            segments.append(segment)
    return "/".join(segments)


def _read_task_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
