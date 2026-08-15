#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent import LocalModelClient
from skill_validation import validate_and_refine


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and refine one Train-derived skill")
    parser.add_argument("--skill", required=True)
    parser.add_argument("--output", default="outputs/skill_generation/validation")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    model = LocalModelClient(
        base_url=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key="local",
        model_id=os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )
    result = validate_and_refine(args.skill, model, args.output, args.max_rounds, args.seed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

