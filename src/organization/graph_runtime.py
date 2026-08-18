"""Online Top-K induced-subgraph extraction and deterministic cycle removal."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from common.schemas import GraphEdge, Skill
from organization.hierarchy import dedupe_skill_ids


EXECUTION_EDGE_TYPES = {"DATA_DEP", "PRECEDES"}
EDGE_PRIORITY = {"DATA_DEP": 2, "PRECEDES": 1}


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
        if current is None or (edge.confidence, edge.support) > (
            current.confidence,
            current.support,
        ):
            candidates[key] = edge

    supporting = sorted(
        (edge for edge in candidates.values() if edge.type == "SUPPORTS"),
        key=lambda edge: (skill_ids.index(edge.source), skill_ids.index(edge.target)),
    )
    execution_candidates = [
        edge for edge in candidates.values() if edge.type in EXECUTION_EDGE_TYPES
    ]
    accepted: list[GraphEdge] = []
    adjacency: dict[str, set[str]] = {skill_id: set() for skill_id in skill_ids}
    for edge in sorted(execution_candidates, key=_sort_key):
        if _reachable(adjacency, edge.target, edge.source):
            dropped.append({**edge.__dict__, "reason": "cycle"})
            continue
        accepted.append(edge)
        adjacency[edge.source].add(edge.target)

    execution_nodes = {
        skill_id for edge in accepted for skill_id in (edge.source, edge.target)
    }
    support_nodes = {
        skill_id for edge in supporting for skill_id in (edge.source, edge.target)
    }
    execution_skill_ids = [
        skill_id for skill_id in skill_ids if skill_id in execution_nodes
    ]
    supporting_only = [
        skill_id for skill_id in skill_ids
        if skill_id not in execution_nodes and skill_id in support_nodes
    ]
    unlinked = [
        skill_id for skill_id in skill_ids
        if skill_id not in execution_nodes and skill_id not in support_nodes
    ]
    return {
        "schema_version": "task_skill_graph_v2",
        "retrieved_skill_ids": skill_ids,
        "nodes": skill_ids,
        "execution_edges": [edge.__dict__ for edge in accepted],
        "supporting_edges": [edge.__dict__ for edge in supporting],
        "edges": [edge.__dict__ for edge in accepted + supporting],
        "topological_layers": (
            _topological_layers(execution_skill_ids, accepted)
            if execution_skill_ids else []
        ),
        "supporting_only_candidates": supporting_only,
        "unlinked_candidates": unlinked,
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
    ranks = {
        skill_id: rank
        for rank, skill_id in enumerate(dag.get("retrieved_skill_ids", []), start=1)
    }
    lines = ["Retrieved Skill Graph", "Execution DAG:"]
    layers = dag.get("topological_layers", [])
    if layers:
        for index, layer in enumerate(layers):
            lines.append(f"Layer {index}:")
            for skill_id in layer:
                lines.append(f"- [{skill_id}] {_name(skill_id, library, names)}")
    else:
        lines.append("- no evidenced execution relations")
    lines.append("Execution relations:")
    execution_edges = dag.get("execution_edges", [])
    if execution_edges:
        lines.extend(
            f"{edge['source']} -> {edge['target']} [{edge['type']}]"
            for edge in execution_edges
        )
    else:
        lines.append("- none")
    lines.append("Supporting-only candidates:")
    supporting_only = dag.get("supporting_only_candidates", [])
    if supporting_only:
        for skill_id in supporting_only:
            lines.append(
                f"- [{skill_id}] {_name(skill_id, library, names)} "
                f"(retrieval rank: {ranks[skill_id]})"
            )
    else:
        lines.append("- none")
    lines.append("Supporting relations:")
    supporting_edges = dag.get("supporting_edges", [])
    if supporting_edges:
        lines.extend(
            f"{edge['source']} supports {edge['target']}"
            for edge in supporting_edges
        )
    else:
        lines.append("- none")
    lines.append("Unlinked candidates:")
    unlinked = dag.get("unlinked_candidates", [])
    if unlinked:
        for skill_id in unlinked:
            lines.append(
                f"- [{skill_id}] {_name(skill_id, library, names)} "
                f"(retrieval rank: {ranks[skill_id]})"
            )
    else:
        lines.append("- none")
    return "\n".join(lines)


def _name(
    skill_id: str, library: Mapping[str, Skill], names: Mapping[str, Any]
) -> str:
    skill = library.get(skill_id)
    return skill.name if skill else str(names.get(skill_id, skill_id))


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
