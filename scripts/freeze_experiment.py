#!/usr/bin/env python3
"""Decision-complete freeze command with required experiment artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from retrieval.bridge import create_freeze_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="append", required=True, help="SPLIT=PATH")
    parser.add_argument("--model-metadata", required=True)
    parser.add_argument(
        "--graph-evidence",
        default=ROOT / "organization" / "train_graph_evidence.json",
    )
    parser.add_argument(
        "--fcsr-manifest",
        default=ROOT.parent / "fcsr" / "checkpoints" / "fcsr" / "manifest.json",
    )
    parser.add_argument("--output", default="freeze_manifest.json")
    args = parser.parse_args()
    artifacts = {
        "library_manifest": ROOT / "skills" / "manifest.json",
        "hierarchy": ROOT / "organization" / "global_hierarchy.json",
        "graph": ROOT / "organization" / "global_graph.json",
        "graph_evidence": args.graph_evidence,
        "model_config": ROOT / "configs" / "model.yaml",
        "agent_config": ROOT / "configs" / "appworld.yaml",
        "skill_config": ROOT / "configs" / "skills.yaml",
        "experiment_config": ROOT / "configs" / "experiment.yaml",
        "react_prompt": ROOT / "configs" / "react_prompt.txt",
        "model_metadata": args.model_metadata,
        "fcsr_manifest": args.fcsr_manifest,
    }
    for value in args.snapshot:
        split, path = value.split("=", 1)
        artifacts[f"{split}_snapshots"] = path
    metadata = {
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "seeds": [42, 43, 44],
        "conditions": ["No-Skill", "Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD"],
        "retrieval": {"rrf_depth": 100, "rrf_k": 60, "top_50": 50, "rerank_top_20": 20, "snapshot_top_k": 5},
        "fcsr_checkpoint": str(Path(args.fcsr_manifest).resolve().parent),
    }
    result = create_freeze_manifest(artifacts, metadata, args.output)
    print(json.dumps({"freeze_hash": result["freeze_hash"], "artifacts": len(artifacts)}, indent=2))


if __name__ == "__main__":
    main()
