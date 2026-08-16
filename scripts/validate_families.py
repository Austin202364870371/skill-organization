#!/usr/bin/env python3
"""Run one resumable shard of family B/C validation."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent import LocalModelClient
from family_validation import validate_family_shard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="skills/candidates")
    parser.add_argument("--split", default="outputs/skill_build/family_split.json")
    parser.add_argument("--output", default="outputs/skill_build/validation")
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--num-shards", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    model = LocalModelClient(
        base_url=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key=os.environ.get("MODEL_API_KEY", "local"),
        model_id=os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )
    result = validate_family_shard(
        args.candidates, args.split, args.output, model,
        args.shard_index, args.num_shards, args.seed,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
