"""The eight preregistered metrics and paired summary helpers."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean, median
from typing import Any, Iterable


METRIC_NAMES = (
    "tgc",
    "sgc",
    "success_rate",
    "total_tokens",
    "execution_steps",
    "wall_clock_time",
    "skill_utilization_rate",
    "unique_skills_loaded",
)


def run_metrics(record: dict[str, Any]) -> dict[str, float]:
    exposed = set(record.get("exposed_skill_ids", []))
    used = set(record.get("used_skill_ids", [])) & exposed
    loaded = {
        event.get("skill_id")
        for event in record.get("skill_load_events", [])
        if event.get("status") == "loaded"
    }
    input_tokens = float(record.get("input_tokens", 0))
    output_tokens = float(record.get("output_tokens", 0))
    return {
        "tgc": float(record.get("tgc", 0.0)),
        "sgc": float(record.get("sgc", 0.0)),
        "success_rate": float(bool(record.get("success", False))),
        "total_tokens": input_tokens + output_tokens,
        "execution_steps": float(record.get("execution_steps", 0)),
        "wall_clock_time": float(record.get("wall_clock_time", 0.0)),
        "skill_utilization_rate": len(used) / len(exposed) if exposed else 0.0,
        "unique_skills_loaded": float(len(loaded)),
    }


def summarize(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    values: dict[str, list[float]] = defaultdict(list)
    for record in records:
        for name, value in run_metrics(record).items():
            values[name].append(value)
    return {name: _describe(values.get(name, [])) for name in METRIC_NAMES}


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

