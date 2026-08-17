"""Side-effect-free progressive disclosure controller."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import monotonic
from typing import Mapping

from common.schemas import OrganizationView, Skill


@dataclass(frozen=True)
class LoadEvent:
    skill_id: str
    step: int
    elapsed_seconds: float
    status: str


class SkillLoader:
    def __init__(self, view: OrganizationView, library: Mapping[str, Skill]) -> None:
        self.view = view
        self.library = library
        self.loaded: set[str] = set()
        self.events: list[LoadEvent] = []
        self.started_at = monotonic()

    def load(self, skill_id: str, step: int) -> str:
        if not self.view.loader_enabled:
            return self._record(skill_id, step, "disabled", "Skill loading is disabled for this condition.")
        if skill_id not in self.view.allowed_skill_ids:
            return self._record(skill_id, step, "forbidden", f"Unknown or unavailable skill: {skill_id}")
        if skill_id in self.loaded:
            return self._record(skill_id, step, "already_loaded", f"Skill {skill_id} is already loaded.")
        skill = self.library[skill_id]
        self.loaded.add(skill_id)
        return self._record(skill_id, step, "loaded", f"SKILL {skill_id}: {skill.name}\n{skill.body}")

    def event_dicts(self) -> list[dict[str, object]]:
        return [asdict(event) for event in self.events]

    def _record(self, skill_id: str, step: int, status: str, response: str) -> str:
        self.events.append(LoadEvent(skill_id, step, monotonic() - self.started_at, status))
        return response
