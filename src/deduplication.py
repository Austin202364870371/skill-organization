"""Conservative duplicate discovery: exact merges, semantic candidates for review."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any, Mapping

from schemas import Contract, Skill


def duplicate_report(
    library: Mapping[str, Skill],
    contracts: Mapping[str, Contract],
    embeddings: Mapping[str, list[float]] | None = None,
    threshold: float = 0.90,
) -> dict[str, Any]:
    exact: dict[str, list[str]] = defaultdict(list)
    for skill in library.values():
        exact[_normalize(skill.body)].append(skill.skill_id)
    exact_groups = [sorted(ids) for ids in exact.values() if len(ids) > 1]
    candidates = []
    if embeddings:
        ids = sorted(set(library) & set(embeddings))
        for index, left in enumerate(ids):
            for right in ids[index + 1:]:
                left_apps = set(contracts[left].apps)
                right_apps = set(contracts[right].apps)
                if left_apps and right_apps and not left_apps & right_apps:
                    continue
                score = cosine(embeddings[left], embeddings[right])
                if score >= threshold:
                    candidates.append({
                        "left": left, "right": right, "similarity": score,
                        "app_overlap": sorted(left_apps & right_apps), "decision": "human_review_required",
                    })
    return {
        "exact_duplicate_groups": exact_groups,
        "semantic_review_candidates": candidates,
        "automatic_merge_policy": "exact_normalized_body_only",
        "semantic_threshold": threshold,
    }


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("embedding vectors must have the same non-zero dimension")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("zero embedding vector")
    return numerator / (left_norm * right_norm)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()

