"""Integrity checks for the fixed main-experiment Skill Library."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from common.utils import read_json


GENERIC_SKILL_NAMES = {"skill", "skill.md", "when to use"}


def parse_skill_frontmatter(text: str) -> tuple[str, str]:
    """Parse one strict leading frontmatter block without accepting nested blocks."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md lacks leading YAML frontmatter")
    try:
        closing = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError("SKILL.md frontmatter is not closed") from error
    values: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    name = values.get("name", "").strip()
    description = values.get("description", "").strip()
    if not name or not description:
        raise ValueError("SKILL.md frontmatter requires name and description")
    if name.casefold() in GENERIC_SKILL_NAMES:
        raise ValueError(f"SKILL.md uses a generic name: {name}")
    if sum(line.strip() == "---" for line in lines[closing + 1 :]) >= 2:
        raise ValueError("SKILL.md contains a second frontmatter block")
    return name, description


def validate_library(
    root: str | Path, minimum: int = 40, maximum: int = 60
) -> dict[str, int]:
    directories = [
        path
        for path in Path(root).iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    ]
    if not minimum <= len(directories) <= maximum:
        raise ValueError(
            f"frozen library must contain {minimum} to {maximum} skills, "
            f"found {len(directories)}"
        )
    invalid = []
    metadata_by_id: dict[str, Mapping[str, Any]] = {}
    for directory in directories:
        try:
            metadata = read_json(directory / "metadata.json")
            parse_skill_frontmatter(
                (directory / "SKILL.md").read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValueError, TypeError):
            invalid.append(directory.name)
            continue
        metadata_by_id[directory.name] = metadata
        required = (
            directory / "references" / "api_patterns.json",
            directory / "references" / "examples.json",
            directory / "references" / "evidence.json",
        )
        if (
            metadata.get("skill_id") != directory.name
            or metadata.get("source_split") != "train"
            or metadata.get("validation_status") != "grounded"
            or any(not path.is_file() for path in required)
            or (directory / "contract.json").exists()
        ):
            invalid.append(directory.name)
            continue
        if metadata.get("inclusion_policy") == "train_grounded_v2":
            if not _source_records_match_v2(directory.name, metadata, read_json(directory / "references" / "evidence.json")):
                invalid.append(directory.name)
                continue
        else:
            if metadata.get("inclusion_policy") != "train_grounded_v1":
                invalid.append(directory.name)
                continue
            try:
                evidence = read_json(directory / "references" / "evidence.json")
                read_json(directory / "references" / "api_patterns.json")
                read_json(directory / "references" / "examples.json")
            except (FileNotFoundError, ValueError, TypeError):
                invalid.append(directory.name)
                continue
            if not _source_records_match(directory.name, metadata, evidence):
                invalid.append(directory.name)
    family_ids = sorted({
        str(metadata.get("family_id"))
        for metadata in metadata_by_id.values()
        if metadata.get("inclusion_policy") == "train_grounded_v2"
    })
    v2_skills = {
        skill_id: metadata
        for skill_id, metadata in metadata_by_id.items()
        if metadata.get("inclusion_policy") == "train_grounded_v2"
    }
    if v2_skills:
        for skill_id, metadata in v2_skills.items():
            if metadata.get("candidate_type") != "core":
                invalid.append(skill_id)
            if metadata.get("skill_role") not in {"primary", "secondary"}:
                invalid.append(skill_id)
        for family_id in family_ids:
            roles = {
                metadata.get("skill_role")
                for metadata in v2_skills.values()
                if metadata.get("family_id") == family_id
            }
            if not roles or not roles.issubset({"primary", "secondary"}):
                invalid.append(str(family_id))
    if invalid:
        raise ValueError(
            f"library contains invalid skills: {sorted(set(invalid))[:20]}"
        )
    return {"skills": len(directories), "validated": len(directories)}


def _source_records_match_v2(
    skill_id: str, metadata: Mapping[str, Any], evidence: Mapping[str, Any]
) -> bool:
    split_roles = evidence.get("split_roles", {}) if isinstance(evidence, Mapping) else {}
    return (
        metadata.get("candidate_type") == "core"
        and metadata.get("family_id") == split_roles.get("family_id")
        and metadata.get("generation_task") == split_roles.get("generation_task")
        and metadata.get("refinement_task") == split_roles.get("refinement_task")
        and metadata.get("acceptance_task") == split_roles.get("acceptance_task")
        and metadata.get("reference_hash") == evidence.get("reference_hash")
    )


def _source_records_match(
    skill_id: str, metadata: Mapping[str, Any], evidence: Mapping[str, Any]
) -> bool:
    if metadata.get("candidate_type") == "reusable_subskill":
        proposal = evidence.get("proposal", {})
        return (
            isinstance(proposal, Mapping)
            and proposal.get("proposal_id") == skill_id
            and set(proposal.get("supporting_core_ids", []))
            == set(metadata.get("supporting_core_ids", []))
        )
    family_id = metadata.get("family_id")
    expected = {
        "family_id": family_id,
        "generation_task": f"{family_id}_1",
        "refinement_task": f"{family_id}_2",
        "acceptance_task": f"{family_id}_3",
    }
    split_roles = evidence.get("split_roles", {})
    return (
        isinstance(split_roles, Mapping)
        and all(
            metadata.get(key) == value and split_roles.get(key) == value
            for key, value in expected.items()
        )
        and metadata.get("reference_hash") == evidence.get("reference_hash")
    )
