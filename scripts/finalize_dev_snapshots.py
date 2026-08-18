#!/usr/bin/env python3
"""Build and audit frozen Top-5 Dev snapshots from FCSR reranker output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from common.utils import file_hash, read_json, read_jsonl, write_json
from retrieval.bridge import build_snapshots, load_snapshots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--library-manifest", default="skills/manifest.json")
    parser.add_argument("--fcsr-manifest", required=True)
    parser.add_argument("--provenance-output", required=True)
    parser.add_argument("--snapshot-output", required=True)
    args = parser.parse_args()

    library_manifest = read_json(args.library_manifest)
    allowed = {item["skill_id"] for item in library_manifest["skills"]}
    query_records = list(read_jsonl(args.queries))
    if len(query_records) != 57:
        raise ValueError(f"Dev query count must be 57, found {len(query_records)}")
    if len({item["task_id"] for item in query_records}) != 57:
        raise ValueError("Dev queries contain duplicate task IDs")

    provenance = {
        "schema_version": "fcsr_snapshot_provenance_v2",
        "library_hash": library_manifest["library_hash"],
        "library_manifest_sha256": file_hash(args.library_manifest),
        "fcsr_manifest_sha256": file_hash(args.fcsr_manifest),
        "queries_sha256": file_hash(args.queries),
        "retrieval": {
            "method": "BM25+FCSR_RRF_then_FCSR_reranker",
            "rrf_depth": 100,
            "rrf_k": 60,
            "retrieval_top_k": 50,
            "rerank_depth": 20,
            "snapshot_top_k": 5,
        },
    }
    write_json(args.provenance_output, provenance, overwrite=False)
    report = build_snapshots(
        args.records,
        args.snapshot_output,
        provenance,
        top_k=5,
    )
    snapshots = load_snapshots(args.snapshot_output)
    if set(snapshots) != {item["task_id"] for item in query_records}:
        raise ValueError("snapshot tasks differ from the 57 frozen Dev queries")
    for task_id, snapshot in snapshots.items():
        if len(snapshot.skills) != 5:
            raise ValueError(f"{task_id} does not contain exactly five Skills")
        if not set(snapshot.skill_ids).issubset(allowed):
            raise ValueError(f"{task_id} contains a Skill outside the frozen Library")
    print(json.dumps({**report, "validated_tasks": len(snapshots)}, indent=2))


if __name__ == "__main__":
    main()
