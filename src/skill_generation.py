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
TITLE_FRONTMATTER = re.compile(r"^---\s*\ntitle:\s*(.+?)\n---\s*\n", re.DOTALL)
WHEN_TO_USE = re.compile(r"## When to Use\s*\n+(.*?)(?=\n## |\Z)", re.DOTALL)
MARKDOWN_TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
DESCRIPTION_SECTION = re.compile(r"^## Description\s*\n+(.*?)(?=\n## |\Z)", re.DOTALL | re.MULTILINE)


def induction_prompt(task: str, reference: dict[str, Any]) -> str:
    return f"""Distill one concise, transferable procedural skill from this successful AppWorld
task and reference trajectory. Do not include instance-specific names, IDs, emails, dates,
answers, or copied task wording. Focus on workflow, API selection, prerequisites, pagination,
disambiguation, failure handling, state consistency, and verification.

Return exactly a SKILL.md. The YAML frontmatter must contain `name` and `description` (not `title`). Use sections: When to Use, Preconditions,
Procedure, Relevant APIs / Tools, Failure Handling, Verification.

TASK:\n{task}\n\nREFERENCE:\n{reference}"""


def refinement_prompt(skill_body: str, feedback: dict[str, Any]) -> str:
    return f"""Refine this procedural AppWorld skill using the execution feedback. Preserve
generality and never add task-specific values or the reference answer. The YAML frontmatter must contain `name` and `description` (not `title`). Return the complete
SKILL.md only.\n\nSKILL:\n{skill_body}\n\nFEEDBACK:\n{feedback}"""


def parse_skill_markdown(skill_id: str, text: str, metadata: dict[str, Any] | None = None) -> Skill:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        _, separator, fenced_body = text.partition("\n")
        if separator:
            text = fenced_body.rsplit("```", 1)[0].strip()
    match = FRONTMATTER.search(text)
    if not match:
        title_match = TITLE_FRONTMATTER.search(text)
        use_match = WHEN_TO_USE.search(text)
        if title_match and use_match:
            name = title_match.group(1).strip().strip("\"'")
            description = " ".join(use_match.group(1).split())
            text = TITLE_FRONTMATTER.sub(
                f"---\nname: {name}\ndescription: {description}\n---\n", text, count=1
            )
            match = FRONTMATTER.search(text)
    if not match:
        normalized = _normalize_unclosed_frontmatter(text)
        if normalized:
            text, match = normalized, FRONTMATTER.search(normalized)
    if not match:
        heading_match = MARKDOWN_TITLE.search(text)
        description_match = DESCRIPTION_SECTION.search(text) or WHEN_TO_USE.search(text)
        if heading_match and description_match:
            name = " ".join(heading_match.group(1).split()).strip("\"'")
            description = " ".join(description_match.group(1).split()).strip("\"'")
            text = f"---\nname: {name}\ndescription: {description}\n---\n\n{text}"
            match = FRONTMATTER.search(text)
    if not match:
        raise ValueError("SKILL.md requires name and description YAML frontmatter")
    name, description = match.group(1).strip(), match.group(2).strip()
    name = name.strip("\"'")
    description = description.strip("\"'")
    body = text
    leaks = leakage_findings(body)
    if leaks:
        raise ValueError(f"skill contains possible instance leakage: {leaks}")
    return Skill(skill_id, name, description, body, metadata or {})


def _normalize_unclosed_frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    name = description = None
    body_start = None
    section_names = {
        "When to Use", "Preconditions", "Procedure", "Relevant APIs / Tools",
        "Failure Handling", "Verification",
    }
    for index, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if stripped.startswith("name:") and name is None:
            name = stripped.split(":", 1)[1].strip().strip("\"'")
        elif stripped.startswith("description:") and description is None:
            value = stripped.split(":", 1)[1].strip()
            if value not in {"|", "|-", "|+", ">", ">-", ">+"}:
                description = value.strip("\"'")
            else:
                parts = []
                for candidate in lines[index + 1:]:
                    if candidate.startswith((" ", "\t")) and candidate.strip():
                        parts.append(candidate.strip())
                    elif parts:
                        break
                description = " ".join(parts)
        label = stripped.removeprefix("## ").removesuffix(":")
        if label in section_names:
            body_start = index
            break
    if not name or not description or body_start is None:
        return None
    body_lines = lines[body_start:]
    body = "\n".join(
        f"## {line.strip().removesuffix(':')}"
        if line.strip().removesuffix(":") in section_names else line
        for line in body_lines
    )
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{body}"


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

