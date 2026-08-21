"""Deterministic Train ground-truth evidence extraction for typed Skill graphs."""

from __future__ import annotations

import ast
import itertools
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from common.utils import file_hash, write_json
from organization.graph_builder import parse_skill_records


MIN_PREREQ_SUPPORT = 2
MIN_PREREQ_RATIO = 0.8
MIN_FLOW_SUPPORT = 2


def extract_train_graph_evidence(
    skill_root: str | Path,
    appworld_root: str | Path,
    output_path: str | Path | None = None,
    split_file: str | Path | None = None,
) -> dict[str, Any]:
    """Extract PREREQ and FLOW evidence from Train GT solution code."""
    records, warnings = parse_skill_records(skill_root)
    appworld_root = Path(appworld_root)
    split_path = Path(split_file) if split_file else (
        appworld_root / "data" / "datasets" / "train.txt"
    )
    task_root = appworld_root / "data" / "tasks"
    task_ids = [
        line.strip()
        for line in split_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    official_train_path = appworld_root / "data" / "datasets" / "train.txt"
    official_train_ids = {
        line.strip()
        for line in official_train_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if (
        not task_ids
        or any(_split_name(task_id) != "train" for task_id in task_ids)
        or not set(task_ids).issubset(official_train_ids)
    ):
        raise ValueError("graph evidence input must contain Train task ids only")

    prereq_observations: dict[frozenset[str], list[dict[str, Any]]] = defaultdict(list)
    flow_observations: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    task_records = []
    rejected = Counter()

    for task_id in task_ids:
        family_id = task_id.rsplit("_", 1)[0]
        family_skills = {
            skill_id: record
            for skill_id, record in records.items()
            if record["family_id"] == family_id
        }
        if not family_skills:
            continue
        solution_path = task_root / task_id / "ground_truth" / "solution.py"
        if not solution_path.is_file():
            warnings.append(f"missing Train GT solution: {task_id}")
            continue
        analysis = analyze_solution(solution_path)
        occurrences = [
            {**occurrence, "api": _api_identifier(occurrence["api"])}
            for occurrence in analysis["occurrences"]
        ]
        non_supervisor = [
            occurrence
            for occurrence in occurrences
            if not _is_supervisor_api(occurrence["api"])
        ]

        matches_by_skill = {}
        intervals = {}
        for skill_id, record in family_skills.items():
            matches = [
                occurrence
                for occurrence in non_supervisor
                if _matches_skill_api(occurrence["api"], record["apis"])
            ]
            if not matches:
                rejected["prereq_no_api_coverage"] += 1
                continue
            matches_by_skill[skill_id] = matches
            intervals[skill_id] = {
                "first_line": min(item["line"] for item in matches),
                "last_line": max(item["line"] for item in matches),
                "occurrence_ids": [item["id"] for item in matches],
                "matched_apis": sorted({item["api"] for item in matches}),
            }

        ordered_starts = sorted(
            (
                (intervals[skill_id]["first_line"], skill_id)
                for skill_id in matches_by_skill
            ),
            key=lambda item: (item[0], item[1]),
        )
        for left, right in itertools.combinations(ordered_starts, 2):
            left_line, left_skill = left
            right_line, right_skill = right
            if left_line == right_line:
                rejected["prereq_equal_start_line"] += 1
                continue
            source, target = (left_skill, right_skill)
            source_line, target_line = left_line, right_line
            prereq_observations[frozenset((left_skill, right_skill))].append({
                "task_id": task_id,
                "family_id": family_id,
                "source": source,
                "target": target,
                "source_first_line": source_line,
                "target_first_line": target_line,
                "source_interval": intervals[source],
                "target_interval": intervals[target],
                "solution_sha256": analysis["solution_sha256"],
            })

        occurrence_to_skills: dict[str, list[str]] = defaultdict(list)
        for skill_id, record in family_skills.items():
            for occurrence in occurrences:
                if _matches_skill_api(occurrence["api"], record["apis"]):
                    occurrence_to_skills[occurrence["id"]].append(skill_id)

        occurrence_lookup = {item["id"]: item for item in occurrences}
        seen_task_dependencies = set()
        for dependency in analysis["dependencies"]:
            source_ids = occurrence_to_skills.get(
                dependency["source_occurrence"], []
            )
            target_ids = occurrence_to_skills.get(
                dependency["target_occurrence"], []
            )
            if len(source_ids) != 1 or len(target_ids) != 1:
                rejected["flow_ambiguous_skill_alignment"] += 1
                continue
            source, target = source_ids[0], target_ids[0]
            if source == target:
                rejected["flow_within_skill"] += 1
                continue
            signature = (source, target, task_id)
            if signature in seen_task_dependencies:
                continue
            seen_task_dependencies.add(signature)
            source_occurrence = occurrence_lookup[dependency["source_occurrence"]]
            target_occurrence = occurrence_lookup[dependency["target_occurrence"]]
            flow_observations[(source, target)].append({
                "task_id": task_id,
                "family_id": family_id,
                "source_api": source_occurrence["api"],
                "target_api": target_occurrence["api"],
                "argument": dependency["argument"],
                "source_line": source_occurrence["line"],
                "target_line": target_occurrence["line"],
                "propagation_chain": dependency["propagation_chain"],
                "solution_sha256": analysis["solution_sha256"],
            })

        task_records.append({
            "task_id": task_id,
            "family_id": family_id,
            "solution_path": str(solution_path.resolve()),
            "solution_sha256": analysis["solution_sha256"],
            "api_occurrences": len(analysis["occurrences"]),
            "skill_intervals": intervals,
        })

    edges = []
    for pair, observations in sorted(
        prereq_observations.items(), key=lambda item: sorted(item[0])
    ):
        counts = Counter((item["source"], item["target"]) for item in observations)
        (source, target), before_count = counts.most_common(1)[0]
        comparable = sum(counts.values())
        ratio = before_count / comparable
        if comparable >= MIN_PREREQ_SUPPORT and ratio >= MIN_PREREQ_RATIO:
            edges.append({
                "source": source,
                "target": target,
                "type": "PREREQ",
                "confidence": ratio,
                "support": comparable,
                "evidence": observations,
            })
        else:
            rejected["prereq_below_threshold"] += 1

    for (source, target), observations in sorted(flow_observations.items()):
        task_support = len({item["task_id"] for item in observations})
        if task_support >= MIN_FLOW_SUPPORT:
            edges.append({
                "source": source,
                "target": target,
                "type": "FLOW",
                "confidence": 1.0,
                "support": task_support,
                "evidence": observations,
            })
        else:
            rejected["flow_below_threshold"] += 1

    edges.sort(key=lambda edge: (edge["source"], edge["target"], edge["type"]))
    result = {
        "schema_version": "train_graph_evidence_v2",
        "source_scope": "train_ground_truth_solutions_only",
        "split": "train",
        "thresholds": {
            "min_prereq_support": MIN_PREREQ_SUPPORT,
            "min_prereq_ratio": MIN_PREREQ_RATIO,
            "min_flow_support": MIN_FLOW_SUPPORT,
        },
        "inputs": {
            "train_split_path": str(split_path.resolve()),
            "train_split_sha256": file_hash(split_path),
            "task_count": len(task_ids),
        },
        "task_records": task_records,
        "edges": edges,
        "candidate_counts": {
            "prereq": len(prereq_observations),
            "flow": len(flow_observations),
        },
        "formal_edge_counts": dict(Counter(edge["type"] for edge in edges)),
        "rejected_counts": dict(sorted(rejected.items())),
        "warnings": warnings,
    }
    if output_path is not None:
        write_json(output_path, result)
    return result


def analyze_solution(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_solution"),
        None,
    )
    if function is None:
        raise ValueError(f"Train GT lacks _solution function: {path}")
    analyzer = _DataflowAnalyzer(function)
    analyzer.run()
    return {
        "solution_sha256": file_hash(path),
        "occurrences": analyzer.occurrences,
        "dependencies": analyzer.dependencies,
    }


class _DataflowAnalyzer:
    """Small conservative intra-procedural API value-flow analyzer."""

    def __init__(self, function: ast.FunctionDef) -> None:
        self.function = function
        nodes = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Attribute) and _api_name(node) is not None
        ]
        nodes.sort(key=lambda node: (node.lineno, node.col_offset, _api_name(node)))
        self.occurrences = [
            {
                "id": f"api_{index:04d}",
                "api": _api_name(node),
                "line": node.lineno,
                "column": node.col_offset,
            }
            for index, node in enumerate(nodes, start=1)
        ]
        self._node_ids = {
            id(node): occurrence["id"]
            for node, occurrence in zip(nodes, self.occurrences)
        }
        self.env: dict[str, set[str]] = {}
        self.dependencies: list[dict[str, Any]] = []
        self._dependency_keys = set()

    def run(self) -> None:
        self._block(self.function.body)

    def _block(self, statements: Iterable[ast.stmt]) -> None:
        for statement in statements:
            self._statement(statement)

    def _statement(self, statement: ast.stmt) -> None:
        self._record_calls(statement)
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            lineage = self._result_lineage(value) if value is not None else set()
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for target in targets:
                self._assign(target, lineage)
        elif isinstance(statement, ast.AugAssign):
            lineage = self._lineage(statement.target) | self._result_lineage(statement.value)
            self._assign(statement.target, lineage)
        elif isinstance(statement, ast.For):
            self._assign(statement.target, self._lineage(statement.iter))
            self._block(statement.body)
            self._block(statement.orelse)
        elif isinstance(statement, ast.While):
            self._block(statement.body)
            self._block(statement.orelse)
        elif isinstance(statement, ast.If):
            original = {key: set(value) for key, value in self.env.items()}
            self._block(statement.body)
            left = {key: set(value) for key, value in self.env.items()}
            self.env = {key: set(value) for key, value in original.items()}
            self._block(statement.orelse)
            for key in set(left) | set(self.env):
                self.env[key] = left.get(key, set()) | self.env.get(key, set())
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            self._block(statement.body)
        elif isinstance(statement, ast.Try):
            self._block(statement.body)
            for handler in statement.handlers:
                self._block(handler.body)
            self._block(statement.orelse)
            self._block(statement.finalbody)
        elif isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            self._update_mutated_receiver(statement.value)

    def _record_calls(self, node: ast.AST) -> None:
        for call in sorted(
            (item for item in ast.walk(node) if isinstance(item, ast.Call)),
            key=lambda item: (item.lineno, item.col_offset),
        ):
            targets = self._call_targets(call)
            if not targets:
                continue
            arguments = [(f"arg_{index}", value) for index, value in enumerate(call.args)]
            arguments.extend((keyword.arg or "**kwargs", keyword.value) for keyword in call.keywords)
            for argument, value in arguments:
                for source in sorted(self._lineage(value) - set(targets)):
                    for target in targets:
                        key = (source, target, argument)
                        if source == target or key in self._dependency_keys:
                            continue
                        self._dependency_keys.add(key)
                        self.dependencies.append({
                            "source_occurrence": source,
                            "target_occurrence": target,
                            "argument": argument,
                            "propagation_chain": [source, argument, target],
                        })

    def _call_targets(self, call: ast.Call) -> list[str]:
        direct = self._node_ids.get(id(call.func))
        if direct:
            return [direct]
        return [
            self._node_ids[id(argument)]
            for argument in call.args
            if isinstance(argument, ast.Attribute) and id(argument) in self._node_ids
        ]

    def _result_lineage(self, node: ast.AST) -> set[str]:
        if isinstance(node, ast.Call):
            targets = self._call_targets(node)
            if targets:
                return set(targets)
        return self._lineage(node)

    def _lineage(self, node: ast.AST | None) -> set[str]:
        if node is None:
            return set()
        occurrence = self._node_ids.get(id(node))
        if occurrence:
            return {occurrence}
        if isinstance(node, ast.Name):
            return set(self.env.get(node.id, set()))
        result = set()
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.Store, ast.Del)):
                result.update(self._lineage(child))
        return result

    def _assign(self, target: ast.AST, lineage: set[str]) -> None:
        if isinstance(target, ast.Name):
            self.env[target.id] = set(lineage)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self._assign(item, lineage)
        else:
            root = _root_name(target)
            if root:
                self.env.setdefault(root, set()).update(lineage)

    def _update_mutated_receiver(self, call: ast.Call) -> None:
        if not isinstance(call.func, ast.Attribute):
            return
        if call.func.attr not in {"add", "append", "extend", "update", "setdefault"}:
            return
        root = _root_name(call.func.value)
        if root:
            for argument in call.args:
                self.env.setdefault(root, set()).update(self._lineage(argument))


def _api_identifier(api: str) -> str:
    return api if api.startswith("apis.") else f"apis.{api}"


def _matches_skill_api(api: str, declared_apis: Iterable[str]) -> bool:
    """Match a GT call to a declared API, including AppWorld login aliases."""
    return any(api in _api_aliases(declared) for declared in declared_apis)


def _api_aliases(api: str) -> set[str]:
    aliases = {api}
    if api.endswith(".login"):
        aliases.add(f"{api.rsplit('.', 1)[0]}.access_token_from")
    return aliases


def _is_supervisor_api(api: str) -> bool:
    return api.startswith("apis.supervisor.")


def _api_name(node: ast.Attribute) -> str | None:
    parts = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name) or current.id != "apis" or len(parts) != 2:
        return None
    method, app = parts
    return f"{app}.{method}"


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _split_name(task_id: str) -> str:
    # Dataset membership, not an ID prefix, is the authority. This guard only
    # rejects malformed task IDs before any task file is read.
    return "train" if "_" in task_id and task_id.rsplit("_", 1)[1].isdigit() else "unknown"
