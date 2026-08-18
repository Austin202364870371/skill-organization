"""Deterministic three-level organization of retrieved Skills."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from common.schemas import Skill


def dedupe_skill_ids(skill_ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for raw in skill_ids:
        skill_id = str(raw)
        if skill_id and skill_id not in seen:
            seen.add(skill_id)
            result.append(skill_id)
    return result


def build_hierarchy(skill_ids: Iterable[str], skill_root: str | Path) -> dict[str, Any]:
    """Build Type -> Primary App -> Skill IDs without changing retrieval order."""
    root = Path(skill_root)
    ordered_ids = dedupe_skill_ids(skill_ids)
    groups: dict[str, dict[str, list[str]]] = {"Core": {}, "Shared": {}}
    names: dict[str, str] = {}
    warnings = []
    for skill_id in ordered_ids:
        directory = root / skill_id
        if not directory.is_dir():
            warnings.append(f"unknown skill_id: {skill_id}")
            continue
        metadata = _read_object(directory / "metadata.json")
        skill_type = (
            "Shared"
            if metadata.get("candidate_type") == "reusable_subskill"
            else "Core"
        )
        app = primary_app(metadata)
        name = _skill_name(directory / "SKILL.md", skill_id)
        names[skill_id] = name
        groups[skill_type].setdefault(app, []).append(skill_id)
    return {
        "schema_version": "skill_hierarchy_v3",
        "retrieved_skill_ids": ordered_ids,
        "hierarchy": groups,
        "names": names,
        "warnings": warnings,
    }


def induce_hierarchy(
    skill_ids: Iterable[str], global_hierarchy: Mapping[str, Any]
) -> dict[str, Any]:
    """Select only retrieved IDs from a prebuilt hierarchy, preserving rank."""
    ordered_ids = dedupe_skill_ids(skill_ids)
    lookup: dict[str, tuple[str, str]] = {}
    raw_groups = global_hierarchy.get("hierarchy", global_hierarchy)
    if isinstance(raw_groups, Mapping):
        for skill_type in ("Core", "Shared"):
            apps = raw_groups.get(skill_type, {})
            if not isinstance(apps, Mapping):
                continue
            for app, ids in apps.items():
                if isinstance(ids, list):
                    for skill_id in ids:
                        if isinstance(skill_id, str):
                            lookup[skill_id] = (skill_type, str(app))
    groups: dict[str, dict[str, list[str]]] = {"Core": {}, "Shared": {}}
    warnings = []
    for skill_id in ordered_ids:
        location = lookup.get(skill_id)
        if location is None:
            warnings.append(f"hierarchy metadata unavailable: {skill_id}")
            continue
        skill_type, app = location
        groups[skill_type].setdefault(app, []).append(skill_id)
    names = global_hierarchy.get("names", {})
    return {
        "retrieved_skill_ids": ordered_ids,
        "hierarchy": groups,
        "names": names if isinstance(names, Mapping) else {},
        "warnings": warnings,
    }


def format_hierarchy_context(
    hierarchy: Mapping[str, Any], library: Mapping[str, Skill]
) -> str:
    lines = ["Retrieved Skill Hierarchy"]
    groups = hierarchy.get("hierarchy", {})
    for skill_type in ("Core", "Shared"):
        apps = groups.get(skill_type, {}) if isinstance(groups, Mapping) else {}
        if not apps:
            continue
        lines.append(f"{skill_type}:")
        for app, skill_ids in apps.items():
            lines.append(f"  {app}:")
            for skill_id in skill_ids:
                skill = library.get(skill_id)
                fallback_names = hierarchy.get("names", {})
                name = skill.name if skill else fallback_names.get(skill_id, skill_id)
                lines.append(f"  - [{skill_id}] {name}")
    if len(lines) == 1:
        lines.append("- no hierarchy metadata available")
    return "\n".join(lines)


def primary_app(metadata: Mapping[str, Any]) -> str:
    apps = _clean_apps(metadata.get("required_apps"))
    if not apps:
        prefixes = []
        for api in _strings(metadata.get("supporting_apis")):
            if "." not in api:
                continue
            prefix = api.split(".", 1)[0].strip()
            if prefix and prefix.lower() != "supervisor":
                prefixes.append(prefix)
        apps = sorted(set(prefixes))
    return apps[0] if apps else "General"


def _clean_apps(value: Any) -> list[str]:
    return sorted({
        app.strip()
        for app in _strings(value)
        if app.strip() and app.strip().lower() != "supervisor"
    })


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _skill_name(path: Path, fallback: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return fallback
    if text.startswith("---\n"):
        header = text.split("---\n", 2)[1]
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            if key.strip() == "name" and value.strip().strip("'\""):
                return value.strip().strip("'\"")
    return fallback
