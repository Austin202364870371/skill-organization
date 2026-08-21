#!/usr/bin/env python3
"""Summarize sampled Skill review runs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default=ROOT / "outputs/skill_build_v2/review/sample_runs")
    parser.add_argument("--output", default=ROOT / "outputs/skill_build_v2/review/sample_run_review.json")
    args = parser.parse_args()
    rows = []
    for path in Path(args.runs).rglob("*.json"):
        if path.name == "summary.json":
            continue
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row.get("review_family"), row.get("review_role"))].append(row)
    families = []
    for (family, role), records in sorted(grouped.items()):
        skill = []
        base = []
        for record in records:
            target = skill if record.get("condition") == "Flat-NoPD" else base
            target.append(record)
        skill_success = sum(r.get("success", False) for r in skill)
        base_success = sum(r.get("success", False) for r in base)
        skill_rcr = sum(r.get("requirement_completion_rate", 0) for r in skill) / max(1, len(skill))
        base_rcr = sum(r.get("requirement_completion_rate", 0) for r in base) / max(1, len(base))
        families.append({
            "family": family,
            "role": role,
            "skill_success": skill_success,
            "base_success": base_success,
            "skill_rcr": round(skill_rcr, 4),
            "base_rcr": round(base_rcr, 4),
            "rcr_delta": round(skill_rcr - base_rcr, 4),
            "task_count": len(skill),
        })
    result = {
        "record_count": len(rows),
        "family_role_count": len(families),
        "families": families,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
