#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_validation import assert_frozen_library_ready
from utils import canonical_hash, file_hash, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a manifest for a validated frozen library")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--output", default="skills/manifest.json")
    args = parser.parse_args()
    status = assert_frozen_library_ready(args.library)
    records = []
    for directory in sorted(Path(args.library).iterdir()):
        if not directory.is_dir() or not (directory / "SKILL.md").exists():
            continue
        metadata = read_json(directory / "metadata.json")
        records.append({
            "skill_id": directory.name,
            "source_task": metadata["source_task"],
            "version": metadata.get("version", 0),
            "validation_status": metadata["validation_status"],
            "skill_sha256": file_hash(directory / "SKILL.md"),
            "contract_sha256": file_hash(directory / "contract.json"),
            "metadata_sha256": file_hash(directory / "metadata.json"),
        })
    manifest = {"schema_version": "skill_library_v1", "count": len(records), "skills": records}
    manifest["library_hash"] = canonical_hash(manifest)
    write_json(args.output, manifest, overwrite=False)
    print(json.dumps({**status, "library_hash": manifest["library_hash"]}, indent=2))


if __name__ == "__main__":
    main()

