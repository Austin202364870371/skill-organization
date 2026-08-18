"""Offline typed graph construction from Train-derived Skill evidence."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from common.schemas import GraphEdge
from common.utils import write_json
from organization.hierarchy import primary_app


MIN_ORDER_SUPPORT = 2
MIN_ORDER_RATIO = 0.8


def build_global_graph(
    skill_root: str | Path,
    output_path: str | Path | None = None,
    trajectory_orders: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    records, warnings = parse_skill_records(skill_root)
    edges = _support_edges(records)
    edges.extend(_explicit_data_dependencies(records))
    edges.extend(_precedence_edges(records, trajectory_orders))
    edges = _unique_edges(edges)
    graph = {
        "schema_version": "typed_skill_graph_v3",
        "source_scope": "train_derived_skill_library_only",
        "thresholds": {
            "min_order_support": MIN_ORDER_SUPPORT,
            "min_order_ratio": MIN_ORDER_RATIO,
        },
        "nodes": [
            {"id": record["id"], "name": record["name"], "type": record["type"]}
            for record in records.values()
        ],
        "edges": [edge.__dict__ for edge in edges],
        "warnings": warnings,
    }
    validate_global_graph(graph)
    if output_path is not None:
        write_json(output_path, graph)
    return graph


def parse_skill_records(
    skill_root: str | Path,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    records: dict[str, dict[str, Any]] = {}
    warnings = []
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
        apps = _apps(metadata)
        trajectory_apis = _strings(api_patterns.get("required_apis"))
        explicit_sequences = _sequences(api_patterns.get("api_sequences"))
        if trajectory_apis:
            explicit_sequences.append(trajectory_apis)
        source_tasks = _source_tasks(metadata, evidence)
        source_families = _source_families(metadata, evidence)
        supporting_apis = _strings(
            metadata.get("supporting_apis") or api_patterns.get("supporting_apis")
        )
        records[skill_id] = {
            "id": skill_id,
            "name": _skill_name(directory / "SKILL.md", skill_id),
            "type": (
                "Shared"
                if metadata.get("candidate_type") == "reusable_subskill"
                else "Core"
            ),
            "apps": apps,
            "apis": sorted(set(trajectory_apis + supporting_apis)),
            "trajectory_apis": trajectory_apis,
            "source_tasks": source_tasks,
            "source_families": source_families,
            "api_sequences": explicit_sequences,
            "supporting_apis": supporting_apis,
            "supporting_core_ids": _strings(metadata.get("supporting_core_ids")),
            "data_dependencies": _dependency_records(metadata, api_patterns, evidence),
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
    # Cycles are deliberately legal in the offline global graph.


def _support_edges(records: Mapping[str, Mapping[str, Any]]) -> list[GraphEdge]:
    edges = []
    shared_records = [record for record in records.values() if record["type"] == "Shared"]
    core_records = [record for record in records.values() if record["type"] == "Core"]
    for shared in shared_records:
        for core in core_records:
            evidence = []
            support = 0
            shared_families = set(shared["source_families"])
            core_families = set(core["source_families"])
            shared_tasks = set(shared["source_tasks"])
            core_tasks = set(core["source_tasks"])
            common_families = sorted(shared_families & core_families)
            common_tasks = sorted(shared_tasks & core_tasks)
            matched_apis = sorted(
                set(shared["supporting_apis"]) & set(core["trajectory_apis"])
            )
            if (common_families or common_tasks) and matched_apis:
                support += len(matched_apis)
                evidence.append({
                    "condition": "shared_source_and_api_in_successful_trajectory",
                    "source_families": common_families,
                    "source_tasks": common_tasks,
                    "matched_apis": matched_apis,
                })
            subsequences = [
                sequence
                for sequence in shared["api_sequences"]
                if sequence
                and any(
                    _is_subsequence(sequence, core_sequence)
                    for core_sequence in core["api_sequences"]
                )
            ]
            if subsequences:
                support += len(subsequences)
                evidence.append({
                    "condition": "shared_api_sequence_is_core_subsequence",
                    "matched_sequences": subsequences,
                })
            if not evidence:
                continue
            denominator = max(
                1, len(shared["supporting_apis"]) + len(shared["api_sequences"])
            )
            edges.append(
                GraphEdge(
                    source=shared["id"],
                    target=core["id"],
                    type="SUPPORTS",
                    confidence=min(1.0, support / denominator),
                    support=support,
                    evidence=evidence,
                )
            )
    return edges


def _explicit_data_dependencies(
    records: Mapping[str, Mapping[str, Any]],
) -> list[GraphEdge]:
    edges = []
    for record in records.values():
        for dependency in record["data_dependencies"]:
            source = dependency.get("producer_skill_id")
            target = dependency.get("consumer_skill_id")
            output = dependency.get("output")
            input_name = dependency.get("input")
            if (
                source not in records
                or target not in records
                or source == target
                or not isinstance(output, str)
                or not isinstance(input_name, str)
            ):
                continue
            support = _positive_int(dependency.get("support"), 1)
            confidence = _probability(dependency.get("confidence"), 1.0)
            edges.append(
                GraphEdge(
                    source=source,
                    target=target,
                    type="DATA_DEP",
                    confidence=confidence,
                    support=support,
                    evidence=[{
                        "condition": "explicit_producer_consumer_reference",
                        "output": output,
                        "input": input_name,
                    }],
                )
            )
    return edges


def _precedence_edges(
    records: Mapping[str, Mapping[str, Any]],
    trajectory_orders: Iterable[Mapping[str, Any]],
) -> list[GraphEdge]:
    pair_counts: Counter[tuple[str, str]] = Counter()
    cooccurrence: Counter[frozenset[str]] = Counter()
    for raw in trajectory_orders:
        if not isinstance(raw, Mapping):
            raise ValueError("trajectory order evidence must explicitly declare split=train")
        split = raw.get("split")
        if split != "train":
            raise ValueError(f"non-Train trajectory forbidden in graph build: {split}")
        evidence_type = raw.get("evidence_type")
        successful = raw.get("successful", raw.get("success"))
        if successful is not True and evidence_type not in {
            "ground_truth_solution",
            "gt_solution",
        }:
            raise ValueError(
                "PRECEDES evidence must be a successful Train trajectory or GT solution"
            )
        order = raw.get("skill_ids", [])
        ordered = [
            skill_id for skill_id in _dedupe(_strings(order)) if skill_id in records
        ]
        for index, source in enumerate(ordered):
            for target in ordered[index + 1 :]:
                pair_counts[(source, target)] += 1
                cooccurrence[frozenset((source, target))] += 1
    edges = []
    for (source, target), before_count in sorted(pair_counts.items()):
        total = cooccurrence[frozenset((source, target))]
        ratio = before_count / total if total else 0.0
        if total >= MIN_ORDER_SUPPORT and ratio >= MIN_ORDER_RATIO:
            edges.append(
                GraphEdge(
                    source=source,
                    target=target,
                    type="PRECEDES",
                    confidence=ratio,
                    support=total,
                    evidence=[{
                        "condition": "train_successful_trajectory_order",
                        "before_count": before_count,
                        "cooccur_count": total,
                    }],
                )
            )
    return edges


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


def _dependency_records(*objects: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for value in objects:
        raw = value.get("data_dependencies", [])
        if isinstance(raw, list):
            result.extend(item for item in raw if isinstance(item, dict))
    return result


def _is_subsequence(needle: list[str], haystack: list[str]) -> bool:
    iterator = iter(haystack)
    return all(any(candidate == item for candidate in iterator) for item in needle)


def _sequences(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    return [sequence for item in value if (sequence := _strings(item))]


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


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


def _positive_int(value: Any, default: int) -> int:
    return value if isinstance(value, int) and value > 0 else default


def _probability(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if 0 <= number <= 1 else default
