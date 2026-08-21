#!/usr/bin/env python3
"""Static review for Skill Library v2."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from organization.library import parse_skill_frontmatter  # noqa: E402


API_TOKEN = re.compile(r"apis\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+")
TEST_SPLIT = re.compile(r"\b(test_normal|test_challenge)\b", re.IGNORECASE)
CANARY = re.compile(r"appworld:[a-f0-9]{7}:[0-9a-f-]{36}")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def api_tokens_in_text(text: str) -> set[str]:
    return set(API_TOKEN.findall(text))


def answer_strings(family: str, appworld_root: Path) -> set[str]:
    values = set()
    for variant in ("1", "2", "3"):
        path = appworld_root / "data" / "tasks" / f"{family}_{variant}" / "ground_truth" / "answer.json"
        if not path.exists():
            continue
        answer = read_json(path)
        if answer is None:
            continue
        if isinstance(answer, str):
            value = answer.strip()
            if value and len(value) >= 3:
                values.add(value)
        elif isinstance(answer, (list, dict)):
            # For action tasks, answer may be null/None. We only care about strings.
            continue
    return values


def review_family(family: str, library: Path, appworld_root: Path) -> dict:
    issues = []
    warnings = []
    skills = {}
    for role in ("primary", "secondary"):
        skill_id = f"{family}-{role}"
        directory = library / skill_id
        if not directory.is_dir():
            warnings.append({"skill_id": skill_id, "level": "warning", "message": "skill role intentionally omitted"})
            continue
        skill_md = directory / "SKILL.md"
        metadata = read_json(directory / "metadata.json")
        api_patterns = read_json(directory / "references" / "api_patterns.json")
        evidence = read_json(directory / "references" / "evidence.json")
        examples = read_json(directory / "references" / "examples.json")
        if not skill_md.exists():
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "missing SKILL.md"})
            continue
        text = skill_md.read_text(encoding="utf-8")
        try:
            name, description = parse_skill_frontmatter(text)
        except Exception as exc:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": f"invalid frontmatter: {exc}"})
            continue
        if metadata is None:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "missing/invalid metadata"})
            continue
        if metadata.get("skill_id") != skill_id:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "metadata skill_id mismatch"})
        if metadata.get("family_id") != family:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "metadata family_id mismatch"})
        if metadata.get("skill_role") != role:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "metadata skill_role mismatch"})
        if metadata.get("candidate_type") != "core":
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "candidate_type must be core"})
        if metadata.get("inclusion_policy") != "train_grounded_v2":
            warnings.append({"skill_id": skill_id, "level": "warning", "message": "unexpected inclusion_policy"})
        if not metadata.get("required_apps"):
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "required_apps missing"})
        if TEST_SPLIT.search(text):
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "test split leaked into SKILL.md"})
        if CANARY.search(text):
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "canary string leaked into SKILL.md"})
        body_tokens = api_tokens_in_text(text)
        pattern_tokens = set()
        if api_patterns:
            for key in ("required_apis", "supporting_apis", "trajectory_apis"):
                raw = api_patterns.get(key, [])
                if isinstance(raw, list):
                    pattern_tokens.update(item for item in raw if isinstance(item, str))
            for call in api_patterns.get("ground_truth_api_calls", []):
                if isinstance(call, dict) and isinstance(call.get("path"), str):
                    # skip, because these are raw path strings not apis.*
                    pass
        normalized_pattern = {item if item.startswith("apis.") else f"apis.{item}" for item in pattern_tokens}
        normalized_body = {item for item in body_tokens}
        if normalized_body and normalized_pattern and normalized_body != normalized_pattern:
            warnings.append({"skill_id": skill_id, "level": "warning", "message": "SKILL APIs differ from api_patterns"})
        if not normalized_body:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "no apis.* tokens in SKILL.md"})
        if not api_patterns or not api_patterns.get("required_apis"):
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "api_patterns required_apis missing"})
        if examples is None or not isinstance(examples, list) or len(examples) == 0:
            warnings.append({"skill_id": skill_id, "level": "warning", "message": "examples missing"})
        answers = answer_strings(family, appworld_root)
        leaked = sorted({answer for answer in answers if answer and answer in text})
        if leaked:
            issues.append({"skill_id": skill_id, "level": "blocker", "message": "task answer leaked", "values": leaked})
        skills[role] = {"text": text, "name": name, "description": description}
    if "primary" in skills and "secondary" in skills:
        ratio = difflib.SequenceMatcher(None, skills["primary"]["text"], skills["secondary"]["text"]).ratio()
        if ratio > 0.75:
            issues.append({"skill_id": family, "level": "blocker", "message": f"primary/secondary too similar: {ratio:.2f}"})
    return {"family_id": family, "issues": issues, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", default=ROOT / "skills/library_v2")
    parser.add_argument("--appworld-root", default=ROOT / "data/appworld")
    parser.add_argument("--output", default=ROOT / "outputs/skill_build_v2/review/static_review.json")
    args = parser.parse_args()
    library = Path(args.library)
    families = sorted({path.name.split("-", 1)[0] for path in library.iterdir() if path.is_dir()})
    reviews = [review_family(family, library, Path(args.appworld_root)) for family in families]
    issues = [item for review in reviews for item in review["issues"]]
    warnings = [item for review in reviews for item in review["warnings"]]
    result = {
        "library": str(library.resolve()),
        "skill_count": sum(1 for path in library.iterdir() if path.is_dir() and (path / "SKILL.md").exists()),
        "family_count": len(reviews),
        "blocker_count": len(issues),
        "warning_count": len(warnings),
        "families": reviews,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"skill_count": result["skill_count"], "family_count": result["family_count"], "blocker_count": result["blocker_count"], "warning_count": result["warning_count"]}, indent=2))
    if issues:
        print("blockers:")
        for item in issues:
            print(" ", item)


if __name__ == "__main__":
    main()
