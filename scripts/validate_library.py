#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_validation import assert_frozen_library_ready


def main() -> None:
    parser = argparse.ArgumentParser(description="Reject non-Train or non-validated library entries")
    parser.add_argument("--library", default="skills/library")
    args = parser.parse_args()
    print(json.dumps(assert_frozen_library_ready(args.library), indent=2))


if __name__ == "__main__":
    main()

