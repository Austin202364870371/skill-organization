"""Lazy AppWorld adapter so core code remains testable before benchmark installation."""

from __future__ import annotations

import importlib.metadata
import inspect
import os
import platform
import time
from pathlib import Path
from typing import Any

from official_agent import solve_with_official
from organizers import build_view
from schemas import Skill, Snapshot
from skill_loader import SkillLoader
from utils import canonical_hash, write_json


SPLITS = ("train", "dev", "test_normal", "test_challenge")


def require_appworld() -> tuple[Any, Any]:
    try:
        from appworld import AppWorld, load_task_ids
    except ImportError as exc:
        raise RuntimeError("AppWorld is not installed; run the reviewed setup Slurm job first") from exc
    return AppWorld, load_task_ids


def audit_install(root: str | Path, output_dir: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    os.environ["APPWORLD_ROOT"] = str(root)
    AppWorld, load_task_ids = require_appworld()
    output_dir = Path(output_dir)
    counts: dict[str, Any] = {}
    for split in SPLITS:
        ids = list(load_task_ids(split))
        counts[split] = {"count": len(ids), "task_ids_hash": canonical_hash(ids), "sample": ids[:3]}
    install = {
        "python": platform.python_version(),
        "appworld_version": importlib.metadata.version("appworld"),
        "appworld_root": str(root),
        "appworld_class_signature": str(inspect.signature(AppWorld)),
    }
    write_json(output_dir / "install.json", install)
    write_json(output_dir / "datasets.json", counts)
    return {"install": install, "datasets": counts}


def run_task(
    task_id: str,
    split: str,
    condition: str,
    seed: int,
    experiment_name: str,
    snapshot: Snapshot,
    library: dict[str, Skill],
    model: dict[str, Any],
    hierarchy: dict[str, Any] | None = None,
    graph: dict[str, Any] | None = None,
    max_steps: int = 30,
) -> dict[str, Any]:
    AppWorld, _ = require_appworld()
    view = build_view(condition, snapshot, library, hierarchy, graph)
    loader = SkillLoader(view, library)
    started = time.monotonic()
    with AppWorld(task_id=task_id, experiment_name=experiment_name) as world:
        trace = solve_with_official(
            world=world, view=view, loader=loader, model_config=model,
            prompt_file_path=str(Path(__file__).resolve().parents[1] / "configs" / "react_prompt.txt"),
            max_steps=max_steps, seed=seed, experiment_name=experiment_name,
        )
        evaluation = world.evaluate()
        evaluation_dict = serialize_evaluation(evaluation)
    elapsed = time.monotonic() - started
    tgc, requirement_completion_rate, success = extract_scores(evaluation_dict)
    return {
        "task_id": task_id,
        "split": split,
        "condition": condition,
        "seed": seed,
        "snapshot_hash": snapshot.snapshot_hash,
        "retrieved_skill_ids": list(snapshot.skill_ids) if condition != "No-Skill" else [],
        "exposed_skill_ids": list(view.exposed_skill_ids),
        **trace,
        "evaluation": evaluation_dict,
        "tgc": tgc,
        "requirement_completion_rate": requirement_completion_rate,
        "success": success,
        "wall_clock_time": elapsed,
    }


def serialize_evaluation(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    for method in ("model_dump", "to_dict", "dict"):
        candidate = getattr(value, method, None)
        if callable(candidate):
            result = candidate()
            if isinstance(result, dict):
                return result
    result: dict[str, Any] = {}
    for name in ("success", "passes", "failures"):
        if hasattr(value, name):
            item = getattr(value, name)
            result[name] = item() if callable(item) else item
    if not result:
        result["repr"] = repr(value)
    return result


def extract_scores(evaluation: dict[str, Any]) -> tuple[float, float, bool]:
    """Return strict task completion, partial requirement completion, and success.

    AppWorld's official task-goal completion is strict: a task contributes one
    only when every evaluator requirement passes. Scenario-goal completion is a
    dataset-level metric and therefore cannot be computed from one task here.
    """
    passes = evaluation.get("passes", [])
    failures = evaluation.get("failures", [])
    pass_count = len(passes) if isinstance(passes, (list, dict)) else int(passes or 0)
    failure_count = len(failures) if isinstance(failures, (list, dict)) else int(failures or 0)
    has_tests = pass_count + failure_count > 0
    success = bool(evaluation.get("success", has_tests and failure_count == 0))
    requirement_completion_rate = (
        pass_count / (pass_count + failure_count) if has_tests else float(success)
    )
    return float(success), requirement_completion_rate, success
