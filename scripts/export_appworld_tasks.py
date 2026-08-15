#!/usr/bin/env python3
"""Export task instructions as the only FCSR query text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from appworld_runtime import require_appworld
from retrieval_bridge import export_queries
from utils import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True, choices=("dev", "test_normal", "test_challenge"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--inventory")
    args = parser.parse_args()
    AppWorld, load_task_ids = require_appworld()
    records = []
    for task_id in load_task_ids(args.split):
        with AppWorld(task_id=task_id, experiment_name=f"query_export__{args.split}") as world:
            records.append({"task_id": task_id, "instruction": str(world.task.instruction)})
    count = export_queries(records, args.output)
    if args.inventory:
        write_json(args.inventory, {"split": args.split, "count": count, "task_ids": [item["task_id"] for item in records]})
    print(json.dumps({"split": args.split, "count": count, "output": args.output}, indent=2))


if __name__ == "__main__":
    main()

