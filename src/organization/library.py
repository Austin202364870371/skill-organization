"""Integrity checks for the fixed main-experiment Skill Library."""

from __future__ import annotations

from pathlib import Path

from common.utils import read_json


def validate_library(root: str | Path, minimum: int = 40, maximum: int = 60) -> dict[str, int]:
    directories = [
        path for path in Path(root).iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    ]
    if not minimum <= len(directories) <= maximum:
        raise ValueError(
            f"frozen library must contain {minimum} to {maximum} skills, "
            f"found {len(directories)}"
        )
    invalid = []
    for directory in directories:
        metadata = read_json(directory / "metadata.json")
        required = (
            directory / "references" / "api_patterns.json",
            directory / "references" / "examples.json",
            directory / "references" / "evidence.json",
        )
        if (
            metadata.get("source_split") != "train"
            or metadata.get("validation_status") != "grounded"
            or metadata.get("inclusion_policy") != "train_grounded_v1"
            or any(not path.is_file() for path in required)
            or (directory / "contract.json").exists()
        ):
            invalid.append(directory.name)
    if invalid:
        raise ValueError(f"library contains invalid skills: {invalid[:20]}")
    return {"skills": len(directories), "validated": len(directories)}
