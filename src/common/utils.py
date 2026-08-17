"""Small deterministic I/O helpers shared by the experiment pipeline."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Iterator


TEST_SPLITS = frozenset({"test_normal", "test_challenge"})


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any, *, overwrite: bool = True) -> None:
    destination = Path(path)
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def read_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: JSONL record must be an object")
            yield value


def write_jsonl(path: str | Path, records: Iterable[dict[str, Any]], *, overwrite: bool = True) -> int:
    destination = Path(path)
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    count = 0
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(canonical_json(record) + "\n")
            count += 1
    os.replace(temporary, destination)
    return count


def require_generation_split(split: str) -> None:
    if split in TEST_SPLITS:
        raise ValueError(f"Skill generation is forbidden for test split: {split}")
    if split != "train":
        raise ValueError(f"Skill generation requires train split, got: {split}")

