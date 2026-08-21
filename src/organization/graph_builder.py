"""Offline typed graph construction from Train-derived Skill evidence."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from common.schemas import GraphEdge
from common.utils import write_json
from organization.hierarchy import primary_app


MIN_RELATED_API_JACCARD = 0.4
SUPERVISOR_PREFIX = "apis.supervisor."


def build_global_graph(
    skill_root: str | Path,
    output_path: str | Path | None = None,
    graph_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    records, warnings = parse_skill_records(skill_root)
    formal_edges = _evidence_edges(records, graph_evidence, warnings)
    related_edges = _related_edges(records)
    graph = {
        "schema_version": "typed_skill_graph_v5",
        "source_scope": "train_ground_truth_evidence_and_skill_metadata",
        "evidence_schema": (
            graph_evidence.get("schema_version") if graph_evidence else None
        ),
        "thresholds": {
            **(dict(graph_evidence.get("thresholds", {})) if graph_evidence else {}),
            "min_related_api_jaccard": MIN_RELATED_API_JACCARD,
        },
        "nodes": [_node_record(record) for record in records.values()],
        "edges": [edge.__dict__ for edge in _unique_edges(formal_edges + related_edges)],
        "warnings": warnings,
    }
    validate_global_graph(graph)
    if output_path is not None:
        write_json(output_path, graph)
    return graph


def _evidence_edges(
    records: Mapping[str, Mapping[str, Any]],
    evidence: Mapping[str, Any] | None,
    warnings: list[str],
) -> list[GraphEdge]:
    if evidence is None:
        warnings.append(
            "no Train graph evidence supplied; graph contains metadata-derived RELATED edges only"
        )
        return []
    if (
        evidence.get("schema_version") != "train_graph_evidence_v2"
        or evidence.get("split") != "train"
        or evidence.get("source_scope") != "train_ground_truth_solutions_only"
    ):
        raise ValueError("global graph requires train_graph_evidence_v2 Train GT evidence")

    result = []
    for raw in evidence.get("edges", []):
        if not isinstance(raw, Mapping):
            raise ValueError("graph evidence edges must be objects")
        edge = GraphEdge(**dict(raw))
        if edge.source not in records or edge.target not in records:
            raise ValueError("graph evidence references an unknown Skill")
        if edge.type not in {"PREREQ", "FLOW"}:
            raise ValueError("formal graph evidence may only contain PREREQ and FLOW edges")
        if edge.support < 2:
            raise ValueError(f"formal {edge.type} edge requires support from two Train GTs")
        result.append(edge)
    return result


def _related_edges(records: Mapping[str, Mapping[str, Any]]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    ids = sorted(records)
    for left_index, left_id in enumerate(ids):
        for right_id in ids[left_index + 1 :]:
            left, right = records[left_id], records[right_id]
            family_evidence = _same_family_evidence(left, right)
            if family_evidence:
                edges.append(
                    GraphEdge(
                        source=left_id,
                        target=right_id,
                        type="RELATED",
                        confidence=1.0,
                        support=max(1, len(family_evidence[0].get("shared_tasks", []))),
                        evidence=family_evidence,
                    )
                )
                continue

            shared_apps = sorted(set(left["apps"]) & set(right["apps"]))
            if not shared_apps:
                continue
            shared_apis = sorted(set(left["app_apis"]) & set(right["app_apis"]))
            jaccard = _jaccard(left["app_apis"], right["app_apis"])
            if jaccard < MIN_RELATED_API_JACCARD:
                continue
            edges.append(
                GraphEdge(
                    source=left_id,
                    target=right_id,
                    type="RELATED",
                    confidence=jaccard,
                    support=max(1, len(shared_apps)),
                    evidence=[{
                        "condition": "shared_app_and_api_overlap",
                        "shared_apps": shared_apps,
                        "shared_apis": shared_apis,
                        "api_jaccard": jaccard,
                    }],
                )
            )
    return edges


def _same_family_evidence(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> list[dict[str, Any]]:
    left_family = left.get("family_id")
    if not isinstance(left_family, str) or not left_family:
        return []
    if left_family != right.get("family_id"):
        return []
    shared_tasks = sorted(
        set(left.get("source_tasks", [])) & set(right.get("source_tasks", []))
    )
    return [{
        "condition": "same_train_family",
        "family_id": left_family,
        "left_role": left.get("skill_role"),
        "right_role": right.get("skill_role"),
        "shared_tasks": shared_tasks,
    }]


def _node_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "name": record["name"],
        "type": record["type"],
        "family_id": record["family_id"],
        "skill_role": record["skill_role"],
        "primary_app": record["primary_app"],
        "required_apis": sorted(record["apis"]),
        "app_apis": sorted(record["app_apis"]),
        "api_sequences": record["api_sequences"],
        "source_tasks": record["source_tasks"],
        "source_families": record["source_families"],
    }


def parse_skill_records(
    skill_root: str | Path,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    records: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    root = Path(skill_root)
    for directory in sorted(root.iterdir()) if root.is_dir() else []:
        if not directory.is_dir() or not (directory / "SKILL.md").exists():
            continue
        skill_id = directory.name
        metadata = _read_object(directory / "metadata.json")
        source_split = metadata.get("source_split")
        if source_split is not None and source_split != "train":
            raise ValueError(
                f"non-Train Skill forbidden in graph build: {skill_id} ({source_split})"
            )
        api_patterns = _read_object(directory / "references" / "api_patterns.json")
        evidence = _read_object(directory / "references" / "evidence.json")
        if not metadata:
            warnings.append(f"missing or malformed metadata: {skill_id}")

        all_apis = _strings(api_patterns.get("required_apis"))
        app_apis = [
            api for api in all_apis if not api.startswith(SUPERVISOR_PREFIX)
        ]
        sequences = _sequences(api_patterns.get("api_sequences"))
        if all_apis:
            sequences.append(all_apis)
        source_tasks = _source_tasks(metadata, evidence)
        source_families = _source_families(metadata, evidence)
        family_id = _first_nonempty(metadata.get("family_id"), source_families)
        skill_role = metadata.get("skill_role")
        if skill_role not in {"primary", "secondary"}:
            skill_role = "primary"

        records[skill_id] = {
            "id": skill_id,
            "name": _skill_name(directory / "SKILL.md", skill_id),
            "type": (
                "Shared"
                if metadata.get("candidate_type") == "reusable_subskill"
                else "Core"
            ),
            "family_id": family_id,
            "skill_role": skill_role,
            "primary_app": primary_app(metadata),
            "apps": _apps(metadata),
            "apis": sorted(set(all_apis)),
            "app_apis": sorted(set(app_apis)),
            "source_tasks": source_tasks,
            "source_families": source_families,
            "api_sequences": sequences,
        }
    return records, warnings


def validate_global_graph(graph: Mapping[str, Any]) -> None:
    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("global graph nodes must be a list")
    node_ids = [
        node.get("id") for node in nodes if isinstance(node, Mapping)
    ]
    if len(node_ids) != len(set(node_ids)) or any(not value for value in node_ids):
        raise ValueError("global graph node ids must be unique and non-empty")
    node_set = set(node_ids)
    for raw in graph.get("edges", []):
        edge = GraphEdge(**raw)
        if edge.source not in node_set or edge.target not in node_set:
            raise ValueError("global graph edge references an unknown node")
    # RELATED cycles are meaningful clusters; strict execution cycles are resolved
    # per Top-K view, so cycles are deliberately legal in the offline global graph.


def _unique_edges(edges: Iterable[GraphEdge]) -> list[GraphEdge]:
    best: dict[tuple[str, str, str], GraphEdge] = {}
    for edge in edges:
        key = (edge.source, edge.target, edge.type)
        current = best.get(key)
        if current is None or (edge.confidence, edge.support) > (
            current.confidence,
            current.support,
        ):
            best[key] = edge
    return [
        best[key]
        for key in sorted(best, key=lambda item: (item[0], item[1], item[2]))
    ]


def _apps(metadata: Mapping[str, Any]) -> list[str]:
    required = sorted({
        value.strip()
        for value in _strings(metadata.get("required_apps"))
        if value.strip() and value.strip().lower() != "supervisor"
    })
    if required:
        return required
    app = primary_app(metadata)
    return [] if app == "General" else [app]


def _source_tasks(
    metadata: Mapping[str, Any], evidence: Mapping[str, Any]
) -> list[str]:
    result = []
    for key in ("generation_task", "refinement_task", "acceptance_task"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            result.append(value)
    split_roles = evidence.get("split_roles", {})
    if isinstance(split_roles, Mapping):
        result.extend(
            value
            for key, value in split_roles.items()
            if key.endswith("_task") and isinstance(value, str) and value
        )
    return _dedupe(result)


def _source_families(
    metadata: Mapping[str, Any], evidence: Mapping[str, Any]
) -> list[str]:
    result = _strings(metadata.get("supporting_family_ids"))
    family_id = metadata.get("family_id")
    if isinstance(family_id, str) and family_id:
        result.append(family_id)
    proposal = evidence.get("proposal", {})
    if isinstance(proposal, Mapping):
        result.extend(_strings(proposal.get("supporting_family_ids")))
    return sorted(set(result))


def _sequences(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    return [sequence for item in value if (sequence := _strings(item))]


def _jaccard(left: Any, right: Any) -> float:
    left_set = set(left or [])
    right_set = set(right or [])
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _first_nonempty(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item:
                    return item
        elif isinstance(value, str) and value:
            return value
    return ""


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
        for line in text.split("---\n", 2)[1].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                name = value.strip().strip("'\"")
                if key.strip() == "name" and name:
                    return name
    return fallback
