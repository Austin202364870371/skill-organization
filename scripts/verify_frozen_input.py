#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from retrieval_bridge import verify_freeze_manifest
from utils import file_hash


def main() -> None:
    parser = argparse.ArgumentParser(description="Require a runtime input to be present in the freeze manifest")
    parser.add_argument("--manifest", default="freeze_manifest.json")
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    manifest = verify_freeze_manifest(args.manifest)
    target = str(Path(args.path).resolve())
    matches = [name for name, item in manifest["artifacts"].items() if item["path"] == target]
    if not matches:
        raise ValueError(f"runtime input is not frozen: {target}")
    print(json.dumps({"artifact": matches[0], "sha256": file_hash(target)}, indent=2))


if __name__ == "__main__":
    main()

