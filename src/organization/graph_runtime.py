"""Online Top-K induced-subgraph extraction and deterministic cycle removal."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from common.schemas import GraphEdge, Skill
from organization.hierarchy import dedupe_skill_ids


EDGE_PRIORITY = {"DATA_DEP": 3, "SUPPORTS": 2, "PRECEDES": 1}


def build_task_dag(
    topk_skill_ids: Iterable[str], global_graph: Mapping[str, Any]
) -> dict[str, Any]:
    skill_ids = dedupe_skill_ids(topk_skill_ids)
    allowed = set(skill_ids)
    known_nodes = {
        node.get("id")
        for node in global_graph.get("nodes", [])
        if isinstance(node, Mapping) and isinstance(node.get("id"), str)
    }
    warnings = [
        f"global graph metadata unavailable: {skill_id}"
        for skill_id in skill_ids
        if known_nodes and skill_id not in known_nodes
    ]
    candidates: dict[tuple[str, str, str], GraphEdge] = {}
    dropped = []
    for raw in global_graph.get("edges", []):
        if not isinstance(raw, Mapping):
            warnings.append("ignored malformed graph edge")
            continue
        source, target = raw.get("source"), raw.get("target")
        if source not in allowed or target not in allowed:
            continue
        if source == target:
            dropped.append({**dict(raw), "reason": "self_loop"})
            continue
        try:
            edge = GraphEdge(
                source=str(source),
                target=str(target),
                type=str(raw.get("type")),
                confidence=float(raw.get("confidence", 0.0)),
                support=int(raw.get("support", 1)),
                evidence=raw.get("evidence", []),
            )
        except (TypeError, ValueError):
            warnings.append(f"ignored malformed graph edge: {source}->{target}")
            continue
        key = (edge.source, edge.target, edge.type)
        current = candidates.get(key)
        if current is None or _sort_key(edge) < _sort_key(current):
            candidates[key] = edge

    accepted: list[GraphEdge] = []
    adjacency: dict[str, set[str]] = {skill_id: set() for skill_id in skill_ids}
    for edge in sorted(candidates.values(), key=_sort_key):
        if _reachable(adjacency, edge.target, edge.source):
            dropped.append({**edge.__dict__, "reason": "cycle"})
            continue
        accepted.append(edge)
        adjacency[edge.source].add(edge.target)

    return {
        "schema_version": "task_skill_dag_v1",
        "retrieved_skill_ids": skill_ids,
        "nodes": skill_ids,
        "edges": [edge.__dict__ for edge in accepted],
        "topological_layers": _topological_layers(skill_ids, accepted),
        "dropped_edges": dropped,
        "warnings": warnings,
    }


def format_graph_context(
    dag: Mapping[str, Any],
    library: Mapping[str, Skill],
    global_graph: Mapping[str, Any] | None = None,
) -> str:
    names = {
        node.get("id"): node.get("name")
        for node in (global_graph or {}).get("nodes", [])
        if isinstance(node, Mapping)
    }
    lines = ["Retrieved Skill DAG"]
    for index, layer in enumerate(dag.get("topological_layers", [])):
        lines.append(f"Layer {index}:")
        for skill_id in layer:
            skill = library.get(skill_id)
            name = skill.name if skill else names.get(skill_id, skill_id)
            lines.append(f"- [{skill_id}] {name}")
    lines.append("Dependencies:")
    edges = dag.get("edges", [])
    if edges:
        lines.extend(
            f"{edge['source']} -> {edge['target']} [{edge['type']}]"
            for edge in edges
        )
    else:
        lines.append("- none")
    return "\n".join(lines)


def _sort_key(edge: GraphEdge) -> tuple[Any, ...]:
    return (
        -EDGE_PRIORITY[edge.type],
        -edge.confidence,
        -edge.support,
        edge.source,
        edge.target,
        edge.type,
    )


def _reachable(adjacency: Mapping[str, set[str]], start: str, target: str) -> bool:
    stack = [start]
    seen = set()
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in seen:
            continue
        seen.add(node)
        stack.extend(sorted(adjacency.get(node, ()), reverse=True))
    return False


def _topological_layers(
    skill_ids: list[str], edges: Iterable[GraphEdge]
) -> list[list[str]]:
    order = {skill_id: index for index, skill_id in enumerate(skill_ids)}
    adjacency: dict[str, set[str]] = {skill_id: set() for skill_id in skill_ids}
    indegree = {skill_id: 0 for skill_id in skill_ids}
    for edge in edges:
        if edge.target not in adjacency[edge.source]:
            adjacency[edge.source].add(edge.target)
            indegree[edge.target] += 1
    remaining = set(skill_ids)
    layers = []
    while remaining:
        layer = sorted(
            (skill_id for skill_id in remaining if indegree[skill_id] == 0),
            key=order.__getitem__,
        )
        if not layer:
            raise ValueError("task graph cycle resolution failed")
        layers.append(layer)
        for source in layer:
            remaining.remove(source)
            for target in adjacency[source]:
                indegree[target] -= 1
    return layers
