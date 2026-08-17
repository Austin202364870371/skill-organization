"""Pure organization views; retrieval membership and rank never change here."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from common.schemas import CONDITIONS, GraphEdge, OrganizationView, Skill, Snapshot


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

    _require_skills(snapshot, skill_library)
    metadata = _flat_metadata(snapshot, skill_library)
    allowed = snapshot.skill_ids
    loader_enabled = condition != "Flat-NoPD"
    structure: dict[str, Any] = {}

    if condition == "Flat-NoPD":
        blocks = ["Available Skills (full instructions):"]
        for skill_id in allowed:
            skill = skill_library[skill_id]
            blocks.append(f"\n[{skill.skill_id}] {skill.name}\nDescription: {skill.description}\n{skill.body}")
        context = "\n".join(blocks)
    else:
        context = metadata + "\n\nLoad instructions with: LOAD_SKILL <skill_id>"
        if condition == "Hierarchy-PD":
            paths = _induced_hierarchy(allowed, hierarchy or {})
            structure = {"paths": paths}
            context += "\n\nHierarchy:\n" + "\n".join(
                f"- {' > '.join(path)}" for path in paths
            )
        elif condition == "Graph-PD":
            edges = induced_edges(allowed, graph or {})
            structure = {"edges": edges}
            relation_lines = [
                f"- {edge['source']} --{edge['relation']}--> {edge['target']}"
                for edge in edges
            ]
            context += "\n\nRelations:\n" + ("\n".join(relation_lines) if relation_lines else "- none")

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


def induced_edges(skill_ids: tuple[str, ...], graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    allowed = set(skill_ids)
    order = {skill_id: rank for rank, skill_id in enumerate(skill_ids)}
    result = []
    for raw in graph.get("edges", []):
        edge = GraphEdge(**raw)
        if edge.source in allowed and edge.target in allowed:
            result.append(raw)
    return sorted(
        result,
        key=lambda item: (
            order[item["source"]], order[item["target"]], item["relation"]
        ),
    )


def _flat_metadata(snapshot: Snapshot, library: Mapping[str, Skill]) -> str:
    lines = ["Available Skills:"]
    for candidate in snapshot.skills:
        skill = library[candidate.skill_id]
        lines.append(f"{candidate.rank}. [{skill.skill_id}] {skill.name}\n   Description: {skill.description}")
    return "\n".join(lines)


def _induced_hierarchy(skill_ids: tuple[str, ...], hierarchy: Mapping[str, Any]) -> list[list[str]]:
    raw_paths = hierarchy.get("paths", {})
    paths = []
    for skill_id in skill_ids:
        path = raw_paths.get(skill_id, ["Uncategorized", skill_id])
        if not isinstance(path, list) or not all(isinstance(item, str) and item for item in path):
            raise ValueError(f"invalid hierarchy path for {skill_id}")
        paths.append([*path, skill_id] if path[-1] != skill_id else path)
    return paths


def _require_skills(snapshot: Snapshot, library: Mapping[str, Skill]) -> None:
    missing = [skill_id for skill_id in snapshot.skill_ids if skill_id not in library]
    if missing:
        raise KeyError(f"snapshot skills missing from library: {missing}")
