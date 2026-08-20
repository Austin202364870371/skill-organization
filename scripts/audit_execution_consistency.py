#!/usr/bin/env python3
"""Audit execution consistency between SKILL.md, metadata, and API patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from common.utils import read_json
from organization.library import parse_skill_frontmatter


API_TOKEN = re.compile(r"apis\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+")


def skill_api_tokens(text: str) -> set[str]:
    return set(API_TOKEN.findall(text))


def pattern_api_tokens(api_patterns: dict) -> set[str]:
    values: list[str] = []
    for key in ("required_apis", "supporting_apis", "trajectory_apis"):
        raw = api_patterns.get(key, [])
        if isinstance(raw, list):
            values.extend(item for item in raw if isinstance(item, str))
    for raw in api_patterns.get("ground_truth_api_calls", []):
        if not isinstance(raw, dict):
            continue
        app = raw.get("app")
        method = raw.get("method")
        if isinstance(app, str) and isinstance(method, str):
            values.append(f"{app}.{method}")
    tokens = {value if "." in value else f"apis.{value}" for value in values}
    return {token.removeprefix("apis.") if token.startswith("apis.") else token for token in tokens}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SKILL/API execution consistency")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--output", default="outputs/audits/execution_consistency.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    issues: list[dict[str, object]] = []
    for directory in sorted(Path(args.library).iterdir()):
        if not directory.is_dir() or not (directory / "SKILL.md").exists():
            continue
        skill_id = directory.name
        metadata = read_json(directory / "metadata.json")
        api_patterns = read_json(directory / "references" / "api_patterns.json")
        text = (directory / "SKILL.md").read_text(encoding="utf-8")
        try:
            parse_skill_frontmatter(text)
        except ValueError as exc:
            issues.append({"skill_id": skill_id, "issue": "invalid_frontmatter", "detail": str(exc)})
        skill_tokens = skill_api_tokens(text)
        pattern_tokens = pattern_api_tokens(api_patterns)
        missing_in_skill = sorted(pattern_tokens - skill_tokens)
        missing_in_patterns = sorted(skill_tokens - pattern_tokens)
        if missing_in_skill:
            issues.append({
                "skill_id": skill_id,
                "issue": "api_pattern_apis_missing_from_skill",
                "apis": missing_in_skill,
            })
        if missing_in_patterns:
            issues.append({
                "skill_id": skill_id,
                "issue": "skill_apis_missing_from_patterns",
                "apis": missing_in_patterns,
            })
        execution_status = metadata.get("execution_validation_status")
        if execution_status in {"b_failed", "c_failed"}:
            issues.append({
                "skill_id": skill_id,
                "issue": "execution_validation_failed",
                "status": execution_status,
                "c_evidence_families": metadata.get("c_evidence_families", []),
            })

    result = {
        "library": str(Path(args.library).resolve()),
        "skill_count": sum(
            1
            for path in Path(args.library).iterdir()
            if path.is_dir() and (path / "SKILL.md").exists()
        ),
        "issue_count": len(issues),
        "issues": issues,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"output already exists: {output} (use --overwrite)")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
