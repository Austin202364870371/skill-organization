"""JSON-only bridge to the frozen FCSR inference pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from schemas import Candidate, Skill, Snapshot
from utils import canonical_hash, file_hash, read_json, read_jsonl, write_json, write_jsonl


def load_skill_library(root: str | Path) -> dict[str, Skill]:
    library: dict[str, Skill] = {}
    for directory in sorted(Path(root).iterdir()):
        if not directory.is_dir() or not (directory / "SKILL.md").exists():
            continue
        metadata_path = directory / "metadata.json"
        metadata = read_json(metadata_path) if metadata_path.exists() else {}
        body = (directory / "SKILL.md").read_text(encoding="utf-8")
        name, description = _frontmatter(body)
        skill = Skill(directory.name, name, description, body, metadata)
        if skill.skill_id in library:
            raise ValueError(f"duplicate skill id: {skill.skill_id}")
        library[skill.skill_id] = skill
    return library


def export_skills(root: str | Path, output: str | Path) -> dict[str, Any]:
    library = load_skill_library(root)
    records = [library[skill_id].retrieval_record() for skill_id in sorted(library)]
    write_jsonl(output, records)
    return {"count": len(records), "library_hash": canonical_hash(records), "output": str(output)}


def export_queries(tasks: Iterable[dict[str, Any]], output: str | Path) -> int:
    records = []
    for task in tasks:
        task_id = task.get("task_id")
        query = task.get("query") or task.get("instruction")
        if not isinstance(task_id, str) or not isinstance(query, str):
            raise ValueError("each query requires task_id and query/instruction")
        records.append({"task_id": task_id, "query": query})
    return write_jsonl(output, records)


def build_snapshots(
    rerank_records: str | Path,
    output: str | Path,
    provenance: dict[str, Any],
    top_k: int = 5,
) -> dict[str, Any]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    snapshots = []
    for record in read_jsonl(rerank_records):
        raw_candidates = record.get("reranked_candidates")
        if not isinstance(raw_candidates, list):
            raise ValueError("reranker record lacks reranked_candidates")
        candidates = []
        for rank, raw in enumerate(raw_candidates[:top_k], start=1):
            score = raw.get("reranker_score", raw.get("score", 0.0))
            candidates.append(Candidate(str(raw["skill_id"]), rank, float(score)))
        snapshot = Snapshot(
            task_id=str(record.get("task_id") or record.get("query_id")),
            query=str(record.get("query") or record.get("task")),
            skills=tuple(candidates),
            provenance=provenance,
        )
        payload = snapshot.payload()
        payload["snapshot_hash"] = snapshot.snapshot_hash
        snapshots.append(payload)
    write_jsonl(output, snapshots)
    return {"count": len(snapshots), "top_k": top_k, "output_hash": file_hash(output)}


def load_snapshots(path: str | Path) -> dict[str, Snapshot]:
    result = {}
    for raw in read_jsonl(path):
        snapshot = Snapshot(
            task_id=raw["task_id"],
            query=raw["query"],
            skills=tuple(Candidate(item["skill_id"], int(item["rank"]), float(item["score"])) for item in raw["skills"]),
            provenance=raw.get("provenance", {}),
        )
        expected = raw.get("snapshot_hash")
        if expected and expected != snapshot.snapshot_hash:
            raise ValueError(f"snapshot hash mismatch for {snapshot.task_id}")
        result[snapshot.task_id] = snapshot
    return result


def create_freeze_manifest(
    artifacts: dict[str, str | Path], metadata: dict[str, Any], output: str | Path
) -> dict[str, Any]:
    resolved = {}
    for name, path in sorted(artifacts.items()):
        candidate = Path(path)
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        resolved[name] = {"path": str(candidate.resolve()), "sha256": file_hash(candidate)}
    manifest = {"schema_version": "freeze_v1", "artifacts": resolved, "metadata": metadata}
    manifest["freeze_hash"] = canonical_hash(manifest)
    write_json(output, manifest, overwrite=False)
    return manifest


def verify_freeze_manifest(path: str | Path) -> dict[str, Any]:
    manifest = read_json(path)
    expected_hash = manifest.pop("freeze_hash", None)
    actual_hash = canonical_hash(manifest)
    manifest["freeze_hash"] = expected_hash
    if expected_hash != actual_hash:
        raise ValueError("freeze manifest content hash mismatch")
    for name, artifact in manifest.get("artifacts", {}).items():
        if file_hash(artifact["path"]) != artifact["sha256"]:
            raise ValueError(f"frozen artifact changed: {name}")
    return manifest


def _frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md lacks YAML frontmatter")
    header = text.split("---\n", 2)[1]
    values = {}
    for line in header.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("'\"")
    if not values.get("name") or not values.get("description"):
        raise ValueError("SKILL.md frontmatter requires name and description")
    return values["name"], values["description"]
