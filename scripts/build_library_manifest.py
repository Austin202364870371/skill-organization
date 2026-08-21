#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from common.utils import canonical_hash, file_hash, read_json, write_json
from organization.library import validate_library


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a manifest for a validated frozen library")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--output", default="skills/manifest.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    status = validate_library(args.library)
    records = []
    for directory in sorted(Path(args.library).iterdir()):
        if not directory.is_dir() or not (directory / "SKILL.md").exists():
            continue
        metadata = read_json(directory / "metadata.json")
        reference_hashes = {
            str(path.relative_to(directory)): file_hash(path)
            for path in sorted((directory / "references").rglob("*"))
            if path.is_file()
        } if (directory / "references").is_dir() else {}
        records.append({
            "skill_id": directory.name,
            "candidate_type": metadata["candidate_type"],
            "family_id": metadata.get("family_id"),
            "skill_role": metadata.get("skill_role"),
            "supporting_family_ids": metadata.get("supporting_family_ids", []),
            "version": metadata.get("version", 0),
            "validation_status": metadata["validation_status"],
            "inclusion_policy": metadata.get("inclusion_policy"),
            "execution_review_status": metadata.get("execution_review_status"),
            "skill_sha256": file_hash(directory / "SKILL.md"),
            "metadata_sha256": file_hash(directory / "metadata.json"),
            "reference_sha256": reference_hashes,
        })
    manifest = {"schema_version": "skill_library_v2", "count": len(records), "skills": records}
    manifest["library_hash"] = canonical_hash(manifest)
    write_json(args.output, manifest, overwrite=args.overwrite)
    print(json.dumps({**status, "library_hash": manifest["library_hash"]}, indent=2))


if __name__ == "__main__":
    main()
