#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contracts import contract_from_mapping
from deduplication import duplicate_report
from retrieval_bridge import load_skill_library
from utils import read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an auditable duplicate review report")
    parser.add_argument("--library", default="skills/library")
    parser.add_argument("--embeddings", help="Optional JSON object mapping skill ids to vectors")
    parser.add_argument("--threshold", type=float, default=0.90)
    parser.add_argument("--output", default="outputs/skill_generation/deduplication.json")
    args = parser.parse_args()
    library = load_skill_library(args.library)
    contracts = {
        skill_id: contract_from_mapping(read_json(Path(args.library) / skill_id / "contract.json"))
        for skill_id in library
    }
    embeddings = read_json(args.embeddings) if args.embeddings else None
    report = duplicate_report(library, contracts, embeddings, args.threshold)
    write_json(args.output, report)
    print(json.dumps({"exact_groups": len(report["exact_duplicate_groups"]), "review_candidates": len(report["semantic_review_candidates"])}, indent=2))


if __name__ == "__main__":
    main()

