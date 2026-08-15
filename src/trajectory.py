"""Schema discovery and normalization for version-dependent AppWorld outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from utils import file_hash, write_json


def inspect_trajectory_tree(root: str | Path, output: str | Path, sample_limit: int = 5) -> dict[str, Any]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(root)
    files = [path for path in root.rglob("*") if path.is_file()]
    suffix_counts: dict[str, int] = {}
    samples = []
    for path in files:
        suffix_counts[path.suffix or "<none>"] = suffix_counts.get(path.suffix or "<none>", 0) + 1
        if len(samples) < sample_limit and path.suffix in {".json", ".jsonl"}:
            samples.append(_inspect_json_file(path, root))
    report = {
        "root": str(root.resolve()),
        "file_count": len(files),
        "suffix_counts": suffix_counts,
        "samples": samples,
    }
    write_json(output, report)
    return report


def normalize_trajectory(path: str | Path, task_id: str | None = None) -> dict[str, Any]:
    path = Path(path)
    raw = _read_json_like(path)
    if isinstance(raw, list):
        container: dict[str, Any] = {"messages": raw}
    elif isinstance(raw, dict):
        container = raw
    else:
        raise ValueError("trajectory root must be an object or list")
    messages = _first_list(container, "messages", "conversation", "trajectory")
    steps = _first_list(container, "steps", "interactions", "records")
    return {
        "task_id": task_id or str(container.get("task_id") or path.parent.name),
        "instruction": str(container.get("instruction") or container.get("task") or ""),
        "messages": messages,
        "steps": steps,
        "claimed_complete": bool(container.get("claimed_complete") or container.get("task_completed")),
        "evaluation": container.get("evaluation", {}),
        "source_path": str(path.resolve()),
        "source_hash": file_hash(path),
    }


def _inspect_json_file(path: Path, root: Path) -> dict[str, Any]:
    try:
        value = _read_json_like(path)
        schema = _shape(value)
        error = None
    except Exception as exc:  # inspection must report malformed files rather than stop
        schema = None
        error = f"{type(exc).__name__}: {exc}"
    return {"path": str(path.relative_to(root)), "hash": file_hash(path), "shape": schema, "error": error}


def _read_json_like(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _shape(value: Any, depth: int = 0) -> Any:
    if depth >= 4:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: _shape(item, depth + 1) for key, item in list(value.items())[:50]}
    if isinstance(value, list):
        return {"type": "list", "length": len(value), "item": _shape(value[0], depth + 1) if value else None}
    return type(value).__name__


def _first_list(container: dict[str, Any], *names: str) -> list[Any]:
    for name in names:
        value = container.get(name)
        if isinstance(value, list):
            return value
    return []

