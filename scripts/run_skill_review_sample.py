#!/usr/bin/env python3
"""Run sampled Skill review on selected Train families using AppWorld + local model."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from common.schemas import Candidate, Snapshot  # noqa: E402
from retrieval.bridge import load_skill_library  # noqa: E402
from runtime.appworld_runtime import run_task  # noqa: E402
from runtime.official_agent import local_model_config  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", default=ROOT / "skills/library_v2")
    parser.add_argument("--output", default=ROOT / "outputs/skill_build_v2/review/sample_runs")
    parser.add_argument("--families", required=True, help="comma-separated family ids")
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--model-id", default="Qwen/Qwen3-Coder-30B-A3B-Instruct")
    parser.add_argument("--base-url", default=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"))
    args = parser.parse_args()

    library = load_skill_library(args.library)
    families = [item.strip() for item in args.families.split(",") if item.strip()]
    seeds = [int(item) for item in args.seeds.split(",")]
    model = local_model_config(args.base_url, args.model_id)
    summaries = []
    for family in families:
        for role in ("primary", "secondary"):
            skill_id = f"{family}-{role}"
            skill = library[skill_id]
            one_library = {skill_id: skill}
            for task_variant in (1, 2, 3):
                task_id = f"{family}_{task_variant}"
                for seed in seeds:
                    for condition in ("No-Skill", "Flat-NoPD"):
                        snapshot = Snapshot(
                            task_id=task_id,
                            query="review sample",
                            skills=(Candidate(skill_id, 1, 1.0),) if condition != "No-Skill" else (),
                        )
                        experiment_name = f"skill_review_v2__{family}__{role}__{condition}__seed_{seed}"
                        started = time.monotonic()
                        record = run_task(
                            task_id=task_id,
                            split="train",
                            condition=condition,
                            seed=seed,
                            experiment_name=experiment_name,
                            snapshot=snapshot,
                            library=one_library,
                            model=model,
                            hierarchy={},
                            graph={},
                            max_steps=args.max_steps,
                        )
                        record["review_family"] = family
                        record["review_role"] = role
                        record["elapsed"] = time.monotonic() - started
                        out = Path(args.output) / family / role / condition / str(seed) / f"{task_id}.json"
                        write_json(out, record)
                        summaries.append({
                            "family": family,
                            "role": role,
                            "condition": condition,
                            "task_id": task_id,
                            "seed": seed,
                            "success": record.get("success"),
                            "rcr": record.get("requirement_completion_rate"),
                            "tokens": record.get("input_tokens", 0) + record.get("output_tokens", 0),
                            "steps": record.get("execution_steps"),
                        })
                        print(json.dumps(summaries[-1], ensure_ascii=False), flush=True)
    write_json(Path(args.output) / "summary.json", {"rows": summaries})


if __name__ == "__main__":
    main()
