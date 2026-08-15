#!/usr/bin/env python3
"""Run one No-Skill Dev task before retrieval assets exist."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from official_agent import local_model_config
from appworld_runtime import require_appworld, run_task
from schemas import Snapshot
from utils import write_json


def main() -> None:
    _, load_task_ids = require_appworld()
    task_id = sorted(load_task_ids("dev"))[0]
    snapshot = Snapshot(task_id=task_id, query="No-Skill smoke test", skills=())
    model = local_model_config(
        os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )
    result = run_task(
        task_id=task_id, split="dev", condition="No-Skill", seed=42,
        experiment_name="skill_organization__dev__no_skill__smoke",
        snapshot=snapshot, library={}, model=model, max_steps=30,
    )
    output = ROOT / "outputs" / "runs" / "smoke" / f"{task_id}.json"
    write_json(output, result, overwrite=False)
    print(json.dumps({"task_id": task_id, "success": result["success"], "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

