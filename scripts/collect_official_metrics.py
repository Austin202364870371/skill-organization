#!/usr/bin/env python3
"""Collect AppWorld's official aggregate TGC/SGC for each condition and seed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from schemas import CONDITIONS
from utils import read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--appworld-root", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seeds", default="42,43,44")
    args = parser.parse_args()
    records = []
    for seed in [int(value) for value in args.seeds.split(",")]:
        for condition in CONDITIONS:
            safe = condition.replace("-", "_").lower()
            experiment = f"skill_organization__{args.split}__{safe}__seed_{seed}"
            path = Path(args.appworld_root) / "experiments" / "outputs" / experiment / "evaluations" / f"{args.split}.json"
            if not path.exists():
                raise FileNotFoundError(path)
            payload = read_json(path)
            aggregate = payload.get("aggregate", payload)
            tgc_percent = _official_value(aggregate, "task_goal_completion", "strict", "tgc")
            sgc_percent = _official_value(
                aggregate, "scenario_goal_completion", "grouped_strict", "sgc"
            )
            records.append({
                "split": args.split, "condition": condition, "seed": seed,
                "tgc": tgc_percent / 100.0, "sgc": sgc_percent / 100.0,
                "official_tgc_percent": tgc_percent,
                "official_sgc_percent": sgc_percent,
                "num_tasks": aggregate.get("num_tasks"), "num_scenarios": aggregate.get("num_scenarios"),
                "source": str(path.resolve()),
            })
    write_json(args.output, {
        "schema_version": "official_appworld_metrics_v2",
        "metric_scale": "proportion",
        "records": records,
    })
    print(json.dumps({"records": len(records), "output": args.output}, indent=2))


def _official_value(aggregate: dict, *names: str) -> float:
    for name in names:
        value = aggregate.get(name)
        if value is not None:
            return float(value)
    raise KeyError(f"official AppWorld aggregate is missing all fields: {names}")


if __name__ == "__main__":
    main()
