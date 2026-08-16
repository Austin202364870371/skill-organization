#!/usr/bin/env python3
"""Mine cross-family reusable subskills and enforce the candidate-count gate."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent import LocalModelClient
from subskill_generation import mine_shared_subskills


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="skills/candidates")
    parser.add_argument("--references", default="outputs/skill_build/references")
    parser.add_argument("--output", default="outputs/skill_build")
    parser.add_argument("--min-total", type=int, default=40)
    parser.add_argument("--max-total", type=int, default=60)
    args = parser.parse_args()
    model = LocalModelClient(
        base_url=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key=os.environ.get("MODEL_API_KEY", "local"),
        model_id=os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )
    report = mine_shared_subskills(
        args.candidates, args.references, args.output, model,
        args.min_total, args.max_total,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["count_gate_passed"] or report["failed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
