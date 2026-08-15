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
            records.append({
                "split": args.split, "condition": condition, "seed": seed,
                "tgc": aggregate.get("tgc"), "sgc": aggregate.get("sgc"),
                "num_tasks": aggregate.get("num_tasks"), "num_scenarios": aggregate.get("num_scenarios"),
                "source": str(path.resolve()),
            })
    write_json(args.output, {"schema_version": "official_appworld_metrics_v1", "records": records})
    print(json.dumps({"records": len(records), "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
