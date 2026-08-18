"""Organization-only views over one frozen ordered retrieval snapshot."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from common.schemas import CONDITIONS, OrganizationView, Skill, Snapshot
from organization.graph_runtime import build_task_dag, format_graph_context
from organization.hierarchy import (
    dedupe_skill_ids,
    format_hierarchy_context,
    induce_hierarchy,
)


def build_view(
    condition: str,
    snapshot: Snapshot,
    skill_library: Mapping[str, Skill],
    hierarchy: Mapping[str, Any] | None = None,
    graph: Mapping[str, Any] | None = None,
) -> OrganizationView:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    if condition == "No-Skill":
        return OrganizationView(condition, "", (), (), False, {}, snapshot.snapshot_hash)

    allowed = tuple(dedupe_skill_ids(snapshot.skill_ids))
    metadata = _flat_metadata(allowed, skill_library)
    loader_enabled = condition != "Flat-NoPD"
    structure: dict[str, Any] = {
        "retrieved_skill_ids": list(allowed),
        "warnings": [
            f"skill metadata unavailable: {skill_id}"
            for skill_id in allowed
            if skill_id not in skill_library
        ],
    }

    if condition == "Flat-NoPD":
        blocks = ["Available Skills (full instructions):"]
        for skill_id in allowed:
            skill = skill_library.get(skill_id)
            if skill is None:
                continue
            blocks.append(
                f"\n[{skill.skill_id}] {skill.name}\n"
                f"Description: {skill.description}\n{skill.body}"
            )
        context = "\n".join(blocks)
    else:
        context = metadata + "\n\nLoad instructions with: LOAD_SKILL <skill_id>"
        if condition == "Hierarchy-PD":
            induced = induce_hierarchy(allowed, hierarchy or {})
            structure = induced
            context += "\n\n" + format_hierarchy_context(induced, skill_library)
        elif condition == "Graph-PD":
            dag = build_task_dag(allowed, graph or {})
            dag["warnings"].extend(
                f"skill metadata unavailable: {skill_id}"
                for skill_id in allowed
                if skill_id not in skill_library
            )
            structure = dag
            context += "\n\n" + format_graph_context(dag, skill_library, graph)

    return OrganizationView(
        condition=condition,
        initial_context=context,
        allowed_skill_ids=allowed,
        exposed_skill_ids=allowed,
        loader_enabled=loader_enabled,
        structure=structure,
        snapshot_hash=snapshot.snapshot_hash,
    )


def assert_fair_views(views: list[OrganizationView]) -> None:
    skill_views = [view for view in views if view.condition != "No-Skill"]
    if not skill_views:
        return
    expected_ids = skill_views[0].allowed_skill_ids
    expected_hash = skill_views[0].snapshot_hash
    for view in skill_views[1:]:
        if view.allowed_skill_ids != expected_ids:
            raise ValueError("skill conditions do not share the same ordered skill ids")
        if view.snapshot_hash != expected_hash:
            raise ValueError("skill conditions do not share the same snapshot hash")


def _flat_metadata(
    skill_ids: tuple[str, ...], library: Mapping[str, Skill]
) -> str:
    lines = ["Available Skills:"]
    for rank, skill_id in enumerate(skill_ids, start=1):
        skill = library.get(skill_id)
        if skill is None:
            continue
        lines.append(
            f"{rank}. [{skill.skill_id}] {skill.name}\n"
            f"   Description: {skill.description}"
        )
    return "\n".join(lines)
