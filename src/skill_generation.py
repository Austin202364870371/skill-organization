"""Prompts, leakage checks, and atomic skill package creation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from schemas import Contract, Skill
from utils import canonical_hash, require_generation_split, write_json


EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.IGNORECASE)
ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
FRONTMATTER = re.compile(r"^---\s*\nname:\s*(.+?)\ndescription:\s*(.+?)\n---\s*\n", re.DOTALL)


def induction_prompt(task: str, reference: dict[str, Any]) -> str:
    return f"""Distill one concise, transferable procedural skill from this successful AppWorld
task and reference trajectory. Do not include instance-specific names, IDs, emails, dates,
answers, or copied task wording. Focus on workflow, API selection, prerequisites, pagination,
disambiguation, failure handling, state consistency, and verification.

Return exactly a SKILL.md with YAML frontmatter and sections: When to Use, Preconditions,
Procedure, Relevant APIs / Tools, Failure Handling, Verification.

TASK:\n{task}\n\nREFERENCE:\n{reference}"""


def refinement_prompt(skill_body: str, feedback: dict[str, Any]) -> str:
    return f"""Refine this procedural AppWorld skill using the execution feedback. Preserve
generality and never add task-specific values or the reference answer. Return the complete
SKILL.md only.\n\nSKILL:\n{skill_body}\n\nFEEDBACK:\n{feedback}"""


def parse_skill_markdown(skill_id: str, text: str, metadata: dict[str, Any] | None = None) -> Skill:
    match = FRONTMATTER.search(text.strip())
    if not match:
        raise ValueError("SKILL.md requires name and description YAML frontmatter")
    name, description = match.group(1).strip(), match.group(2).strip()
    body = text.strip()
    leaks = leakage_findings(body)
    if leaks:
        raise ValueError(f"skill contains possible instance leakage: {leaks}")
    return Skill(skill_id, name, description, body, metadata or {})


def leakage_findings(text: str) -> list[str]:
    findings = []
    for label, pattern in (("email", EMAIL), ("uuid", UUID), ("date", ISO_DATE)):
        if pattern.search(text):
            findings.append(label)
    return findings


def write_skill_package(
    root: str | Path,
    skill: Skill,
    contract: Contract,
    metadata: dict[str, Any],
    *,
    split: str,
) -> Path:
    require_generation_split(split)
    if skill.skill_id != contract.skill_id:
        raise ValueError("skill and contract ids differ")
    destination = Path(root) / skill.skill_id
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"refusing to overwrite skill package: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "SKILL.md").write_text(skill.body.rstrip() + "\n", encoding="utf-8")
    write_json(destination / "contract.json", contract.to_dict(), overwrite=False)
    manifest = {
        **metadata,
        "skill_id": skill.skill_id,
        "source_split": split,
        "content_hash": canonical_hash(skill.retrieval_record()),
    }
    write_json(destination / "metadata.json", manifest, overwrite=False)
    return destination

