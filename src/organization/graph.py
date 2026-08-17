"""Auditable graph construction from Skill provenance and Train workflows."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from common.schemas import GraphEdge


def build_candidate_graph(
    skill_metadata: Mapping[str, Mapping[str, Any]] | Iterable[str],
    trajectory_orders: Iterable[list[str]] = (),
) -> dict[str, Any]:
    if isinstance(skill_metadata, Mapping):
        metadata = {str(skill_id): dict(value) for skill_id, value in skill_metadata.items()}
    else:
        metadata = {str(skill_id): {} for skill_id in skill_metadata}
    nodes = sorted(metadata)
    edges: list[GraphEdge] = []
    seen: set[tuple[str, str, str]] = set()

    for skill_id, value in metadata.items():
        if value.get("candidate_type") != "reusable_subskill":
            continue
        for core_id in value.get("supporting_core_ids", []):
            if core_id in metadata:
                _append_edge(
                    edges,
                    seen,
                    GraphEdge(
                        core_id, skill_id, "semantic",
                        "shared procedure supported by this Train-family core skill",
                        1.0, "train_shared_support",
                    ),
                )

    workflow_counts: dict[tuple[str, str], int] = defaultdict(int)
    for order in trajectory_orders:
        for source, target in zip(order, order[1:]):
            if source != target:
                workflow_counts[(source, target)] += 1
    for (source, target), count in sorted(workflow_counts.items()):
        if source in nodes and target in nodes:
            _append_edge(
                edges,
                seen,
                GraphEdge(source, target, "workflow", f"adjacent in {count} train trajectories", min(1.0, 0.5 + 0.1 * count), "train_trajectory_order"),
            )

    dependency_workflow = [edge for edge in edges if edge.relation in {"dependency", "workflow"}]
    cycle = find_cycle(nodes, dependency_workflow)
    if cycle:
        raise ValueError(f"dependency/workflow graph must be acyclic: {' -> '.join(cycle)}")
    return {"schema_version": "skill_graph_v2", "nodes": nodes, "edges": [edge.__dict__ for edge in edges]}


def validate_graph(graph: Mapping[str, Any]) -> None:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(set(nodes)):
        raise ValueError("graph nodes must be a unique list")
    edges = [GraphEdge(**value) for value in graph.get("edges", [])]
    node_set = set(nodes)
    for edge in edges:
        if edge.source not in node_set or edge.target not in node_set:
            raise ValueError("graph edge references an unknown node")
    cycle = find_cycle(nodes, [edge for edge in edges if edge.relation in {"dependency", "workflow"}])
    if cycle:
        raise ValueError(f"dependency/workflow graph must be acyclic: {' -> '.join(cycle)}")


def find_cycle(nodes: Iterable[str], edges: Iterable[GraphEdge]) -> list[str]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge.source].append(edge.target)
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        stack.append(node)
        for neighbor in adjacency[node]:
            if state.get(neighbor, 0) == 0:
                found = visit(neighbor)
                if found:
                    return found
            elif state.get(neighbor) == 1:
                start = stack.index(neighbor)
                return stack[start:] + [neighbor]
        stack.pop()
        state[node] = 2
        return []

    for node in nodes:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return []


def _append_edge(edges: list[GraphEdge], seen: set[tuple[str, str, str]], edge: GraphEdge) -> None:
    key = (edge.source, edge.target, edge.relation)
    if key not in seen:
        seen.add(key)
        edges.append(edge)
