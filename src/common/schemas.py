"""Validated wire types for skills, snapshots, organization views, and runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from common.utils import canonical_hash


CONDITIONS = ("No-Skill", "Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD")
SKILL_CONDITIONS = CONDITIONS[1:]
EDGE_TYPES = ("dependency", "workflow", "semantic", "alternative")


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class Skill:
    skill_id: str
    name: str
    description: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("skill_id", "name", "description", "body"):
            _nonempty(getattr(self, name), name)

    def retrieval_record(self) -> dict[str, str]:
        return {"skill_id": self.skill_id, "name": self.name, "description": self.description, "body": self.body}


@dataclass(frozen=True)
class Candidate:
    skill_id: str
    rank: int
    score: float

    def __post_init__(self) -> None:
        _nonempty(self.skill_id, "skill_id")
        if self.rank < 1:
            raise ValueError("rank must be positive")


@dataclass(frozen=True)
class Snapshot:
    task_id: str
    query: str
    skills: tuple[Candidate, ...]
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonempty(self.task_id, "task_id")
        _nonempty(self.query, "query")
        ids = [candidate.skill_id for candidate in self.skills]
        ranks = [candidate.rank for candidate in self.skills]
        if len(ids) != len(set(ids)):
            raise ValueError("snapshot contains duplicate skill ids")
        if ranks != list(range(1, len(ranks) + 1)):
            raise ValueError("snapshot ranks must be contiguous and ordered")

    @property
    def skill_ids(self) -> tuple[str, ...]:
        return tuple(candidate.skill_id for candidate in self.skills)

    def payload(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "top_k": len(self.skills),
            "skills": [asdict(candidate) for candidate in self.skills],
            "provenance": self.provenance,
        }

    @property
    def snapshot_hash(self) -> str:
        return canonical_hash(self.payload())


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str
    evidence: str
    confidence: float
    method: str

    def __post_init__(self) -> None:
        if self.relation not in EDGE_TYPES:
            raise ValueError(f"unknown edge type: {self.relation}")
        if self.source == self.target:
            raise ValueError("self edges are forbidden")
        if not 0 <= self.confidence <= 1:
            raise ValueError("edge confidence must be between 0 and 1")
        _nonempty(self.evidence, "evidence")
        _nonempty(self.method, "method")


@dataclass(frozen=True)
class OrganizationView:
    condition: str
    initial_context: str
    allowed_skill_ids: tuple[str, ...]
    exposed_skill_ids: tuple[str, ...]
    loader_enabled: bool
    structure: dict[str, Any]
    snapshot_hash: str

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError(f"unknown condition: {self.condition}")
        if not set(self.exposed_skill_ids).issubset(self.allowed_skill_ids):
            raise ValueError("exposed skills must be allowed")

    @property
    def view_hash(self) -> str:
        return canonical_hash(asdict(self))
