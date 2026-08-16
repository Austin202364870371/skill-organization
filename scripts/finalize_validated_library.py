#!/usr/bin/env python3
"""Promote C-accepted cores and cross-family evidenced subskills."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from family_validation import finalize_validated_library


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="skills/candidates")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--validation", default="outputs/skill_build/validation")
    parser.add_argument("--output", default="outputs/skill_build/validation_report.json")
    args = parser.parse_args()
    result = finalize_validated_library(
        args.candidates, args.library, args.validation, args.output
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
