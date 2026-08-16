"""The eight preregistered metrics and paired summary helpers."""

from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from statistics import mean, median
from typing import Any, Iterable


METRIC_NAMES = (
    "tgc",
    "sgc",
    "success_rate",
    "requirement_completion_rate",
    "total_tokens",
    "execution_steps",
    "wall_clock_time",
    "skill_utilization_rate",
    "unique_skills_loaded",
)

PD_CONDITIONS = {"Flat-PD", "Hierarchy-PD", "Graph-PD"}
TASK_VARIANT = re.compile(r"^(.+)_([1-9]\d*)$")
EXPECTED_SCENARIO_SIZE = 3


def run_metrics(record: dict[str, Any]) -> dict[str, float | None]:
    """Compute per-task metrics; SGC is filled only during scenario aggregation."""
    exposed = set(record.get("exposed_skill_ids", []))
    used = set(record.get("used_skill_ids", [])) & exposed
    loaded = {
        event.get("skill_id")
        for event in record.get("skill_load_events", [])
        if event.get("status") == "loaded"
    }
    input_tokens = float(record.get("input_tokens", 0))
    output_tokens = float(record.get("output_tokens", 0))
    condition = str(record.get("condition", ""))
    return {
        "tgc": float(bool(record.get("success", False))),
        "sgc": None,
        "success_rate": float(bool(record.get("success", False))),
        "requirement_completion_rate": requirement_completion_rate(record),
        "total_tokens": input_tokens + output_tokens,
        "execution_steps": float(record.get("execution_steps", 0)),
        "wall_clock_time": float(record.get("wall_clock_time", 0.0)),
        "skill_utilization_rate": len(used) / len(exposed) if exposed else None,
        "unique_skills_loaded": float(len(loaded)) if condition in PD_CONDITIONS else None,
    }


def summarize(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    records = list(records)
    values: dict[str, list[float]] = defaultdict(list)
    for record in records:
        for name, value in run_metrics(record).items():
            if value is not None and math.isfinite(value):
                values[name].append(value)
    values["sgc"].extend(scenario_outcomes(records).values())
    return {name: _describe(values.get(name, [])) for name in METRIC_NAMES}


def requirement_completion_rate(record: dict[str, Any]) -> float:
    explicit = record.get("requirement_completion_rate")
    if explicit is not None:
        return float(explicit)
    evaluation = record.get("evaluation", {})
    if not isinstance(evaluation, dict):
        return float(bool(record.get("success", False)))
    passes = evaluation.get("passes", [])
    failures = evaluation.get("failures", [])
    pass_count = len(passes) if isinstance(passes, (list, dict)) else int(passes or 0)
    failure_count = len(failures) if isinstance(failures, (list, dict)) else int(failures or 0)
    total = pass_count + failure_count
    return pass_count / total if total else float(bool(record.get("success", False)))


def scenario_id(task_id: str) -> str:
    match = TASK_VARIANT.fullmatch(task_id)
    return match.group(1) if match else task_id


def scenario_outcomes(
    records: Iterable[dict[str, Any]], expected_size: int = EXPECTED_SCENARIO_SIZE
) -> dict[tuple[str, str, int, str], float]:
    """Return strict outcomes only for complete AppWorld scenario groups."""
    groups: dict[tuple[str, str, int, str], dict[str, bool]] = defaultdict(dict)
    for record in records:
        task_id = str(record["task_id"])
        key = (
            str(record.get("split", "")),
            str(record.get("condition", "")),
            int(record.get("seed", 0)),
            scenario_id(task_id),
        )
        groups[key][task_id] = bool(record.get("success", False))
    return {
        (split, condition, seed, scenario): float(all(task_outcomes.values()))
        for (split, condition, seed, scenario), task_outcomes in groups.items()
        if len(task_outcomes) == expected_size
    }


def paired_bootstrap_difference(
    pairs: list[tuple[float, float]], samples: int = 10000, seed: int = 42
) -> dict[str, float]:
    if not pairs:
        raise ValueError("at least one pair is required")
    differences = [right - left for left, right in pairs]
    generator = random.Random(seed)
    estimates = sorted(
        mean(generator.choice(differences) for _ in differences) for _ in range(samples)
    )
    return {
        "difference": mean(differences),
        "ci_low": _percentile(estimates, 0.025),
        "ci_high": _percentile(estimates, 0.975),
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    count = len(p_values)
    for rank, (index, value) in enumerate(indexed):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[index] = running
    return adjusted


def _describe(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": math.nan, "median": math.nan, "q1": math.nan, "q3": math.nan, "count": 0}
    ordered = sorted(values)
    return {
        "mean": mean(values),
        "median": median(values),
        "q1": _percentile(ordered, 0.25),
        "q3": _percentile(ordered, 0.75),
        "count": len(values),
    }


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return math.nan
    position = fraction * (len(values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight
