"""Deterministic hierarchy construction from frozen Skill metadata."""

from __future__ import annotations

from collections.abc import Mapping

from common.schemas import Skill


def build_hierarchy(library: Mapping[str, Skill]) -> dict:
    paths = {}
    for skill_id, skill in library.items():
        metadata = skill.metadata
        apps = metadata.get("required_apps", [])
        if not apps:
            apps = sorted({
                api.split(".", 1)[0]
                for api in metadata.get("supporting_apis", [])
                if isinstance(api, str)
                and "." in api
                and not api.startswith("supervisor.")
            })
        app = apps[0] if apps else "General"
        level = (
            "Shared"
            if metadata.get("candidate_type") == "reusable_subskill"
            else "Core"
        )
        paths[skill_id] = [level, app, skill.name]
    return {"schema_version": "skill_hierarchy_v2", "paths": paths}
