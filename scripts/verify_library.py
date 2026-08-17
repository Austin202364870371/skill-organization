#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from common.utils import file_hash, read_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify every package against the frozen library manifest")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--manifest", default="skills/manifest.json")
    args = parser.parse_args()
    manifest = read_json(args.manifest)
    expected = {item["skill_id"]: item for item in manifest["skills"]}
    actual_ids = {
        path.name for path in Path(args.library).iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }
    if actual_ids != set(expected):
        raise ValueError("library membership differs from frozen manifest")
    for skill_id, item in expected.items():
        directory = Path(args.library) / skill_id
        for filename, key in (
            ("SKILL.md", "skill_sha256"), ("metadata.json", "metadata_sha256"),
        ):
            if file_hash(directory / filename) != item[key]:
                raise ValueError(f"frozen skill package changed: {skill_id}/{filename}")
        expected_references = item.get("reference_sha256", {})
        actual_references = {
            str(path.relative_to(directory)): file_hash(path)
            for path in sorted((directory / "references").rglob("*"))
            if path.is_file()
        } if (directory / "references").is_dir() else {}
        if actual_references != expected_references:
            raise ValueError(f"frozen skill references changed: {skill_id}")
    print(json.dumps({"skills": len(expected), "status": "verified"}, indent=2))


if __name__ == "__main__":
    main()
