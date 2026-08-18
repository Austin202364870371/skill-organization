"""Resumable task grid runner with process-isolated AppWorld instances."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from common.schemas import Skill, Snapshot
from common.utils import write_json
from organization.organizers import assert_fair_views, build_view
from runtime.appworld_runtime import require_appworld, run_task
from runtime.official_agent import local_model_config


def run_grid(
    split: str,
    snapshots: dict[str, Snapshot],
    library: dict[str, Skill],
    conditions: list[str],
    seeds: list[int],
    model_config: dict[str, Any],
    output_root: str | Path,
    hierarchy: dict[str, Any] | None = None,
    graph: dict[str, Any] | None = None,
    max_steps: int = 30,
    workers: int = 1,
    task_limit: int | None = None,
) -> dict[str, int]:
    _, load_task_ids = require_appworld()
    task_ids = list(load_task_ids(split))
    if task_limit is not None:
        task_ids = task_ids[:task_limit]
    missing = [task_id for task_id in task_ids if task_id not in snapshots]
    if missing:
        raise ValueError(f"missing retrieval snapshots for {len(missing)} tasks")
    for task_id in task_ids:
        views = [
            build_view(
                condition,
                snapshots[task_id],
                library,
                hierarchy,
                graph,
            )
            for condition in conditions
        ]
        assert_fair_views(views)
    work, skipped = [], 0
    for task_id in task_ids:
        for seed in seeds:
            for condition in conditions:
                destination = Path(output_root) / split / task_id / str(seed) / f"{condition}.json"
                if destination.exists():
                    skipped += 1
                    continue
                work.append({
                    "task_id": task_id, "split": split, "condition": condition, "seed": seed,
                    "snapshot": snapshots[task_id], "library": library, "model_config": model_config,
                    "hierarchy": hierarchy, "graph": graph, "max_steps": max_steps,
                    "destination": destination,
                })
    completed = 0
    if workers == 1:
        for item in work:
            _run_one(item)
            completed += 1
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as executor:
            futures = [executor.submit(_run_one, item) for item in work]
            for future in as_completed(futures):
                future.result()
                completed += 1
    return {"completed": completed, "skipped": skipped, "failed": 0}


def _run_one(item: dict[str, Any]) -> None:
    config = item["model_config"]
    model = local_model_config(config["base_url"], config["model_id"])
    safe_condition = item["condition"].replace("-", "_").lower()
    name = f"skill_organization__{item['split']}__{safe_condition}__seed_{item['seed']}"
    record = run_task(
        task_id=item["task_id"], split=item["split"], condition=item["condition"],
        seed=item["seed"], experiment_name=name, snapshot=item["snapshot"],
        library=item["library"], model=model, hierarchy=item["hierarchy"], graph=item["graph"],
        max_steps=item["max_steps"],
    )
    write_json(item["destination"], record, overwrite=False)
