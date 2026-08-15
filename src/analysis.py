"""Condition summaries and preregistered paired comparisons."""

from __future__ import annotations

import itertools
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from metrics import METRIC_NAMES, holm_adjust, paired_bootstrap_difference, run_metrics, summarize
from utils import read_json


PRIMARY_COMPARISONS = (
    ("Flat-NoPD", "Flat-PD"),
    ("Flat-PD", "Hierarchy-PD"),
    ("Flat-PD", "Graph-PD"),
    ("Hierarchy-PD", "Graph-PD"),
)


def analyze_runs(root: str | Path, bootstrap_samples: int = 10000) -> dict[str, Any]:
    records = [read_json(path) for path in Path(root).rglob("*.json")]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    indexed: dict[tuple[str, str, int, str], dict[str, float]] = {}
    for record in records:
        split, condition = record["split"], record["condition"]
        groups[(split, condition)].append(record)
        indexed[(split, record["task_id"], int(record["seed"]), condition)] = run_metrics(record)

    summaries = {
        split: {condition: summarize(group) for (group_split, condition), group in groups.items() if group_split == split}
        for split in sorted({key[0] for key in groups})
    }
    comparisons: dict[str, Any] = {}
    for split in summaries:
        split_results = []
        for left, right in PRIMARY_COMPARISONS:
            entry = {"left": left, "right": right, "metrics": {}}
            for metric in METRIC_NAMES:
                pairs = _pairs(indexed, split, left, right, metric)
                if not pairs:
                    continue
                result = paired_bootstrap_difference(pairs, bootstrap_samples)
                result["p_value"] = paired_permutation_p(pairs)
                result["pairs"] = len(pairs)
                entry["metrics"][metric] = result
            split_results.append(entry)
        for metric in METRIC_NAMES:
            available = [entry for entry in split_results if metric in entry["metrics"]]
            adjusted = holm_adjust([entry["metrics"][metric]["p_value"] for entry in available])
            for entry, value in zip(available, adjusted):
                entry["metrics"][metric]["holm_p_value"] = value
        comparisons[split] = split_results
    return {"metric_names": list(METRIC_NAMES), "summaries": summaries, "comparisons": comparisons}


def paired_permutation_p(pairs: list[tuple[float, float]], samples: int = 10000, seed: int = 42) -> float:
    differences = [right - left for left, right in pairs]
    observed = abs(mean(differences))
    if not any(differences):
        return 1.0
    if len(differences) <= 16:
        estimates = (
            abs(mean(sign * value for sign, value in zip(signs, differences)))
            for signs in itertools.product((-1, 1), repeat=len(differences))
        )
        extreme = total = 0
        for estimate in estimates:
            total += 1
            extreme += estimate >= observed - 1e-12
        return extreme / total
    generator = random.Random(seed)
    extreme = 0
    for _ in range(samples):
        estimate = abs(mean(generator.choice((-1, 1)) * value for value in differences))
        extreme += estimate >= observed - 1e-12
    return (extreme + 1) / (samples + 1)


def _pairs(
    indexed: dict[tuple[str, str, int, str], dict[str, float]],
    split: str,
    left: str,
    right: str,
    metric: str,
) -> list[tuple[float, float]]:
    keys = {(key[1], key[2]) for key in indexed if key[0] == split}
    result = []
    for task_id, seed in sorted(keys):
        left_value = indexed.get((split, task_id, seed, left))
        right_value = indexed.get((split, task_id, seed, right))
        if left_value is not None and right_value is not None:
            result.append((left_value[metric], right_value[metric]))
    return result

