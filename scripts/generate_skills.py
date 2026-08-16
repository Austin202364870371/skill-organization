#!/usr/bin/env python3
"""Generate resumable family-level candidate skill packages."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent import LocalModelClient
from family_generation import generate_family_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="outputs/skill_build/family_split.json")
    parser.add_argument("--references", default="outputs/skill_build/references")
    parser.add_argument("--candidates", default="skills/candidates")
    parser.add_argument("--output", default="outputs/skill_build")
    args = parser.parse_args()
    model = LocalModelClient(
        base_url=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key=os.environ.get("MODEL_API_KEY", "local"),
        model_id=os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )
    report = generate_family_candidates(
        args.split, args.references, args.candidates, args.output, model
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
