#!/usr/bin/env python3
"""Command-line entry point for the frozen Skill organization experiment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from common.schemas import CONDITIONS
from common.utils import read_json, write_json
from evaluation.analysis import analyze_runs
from organization.graph_builder import build_global_graph
from organization.hierarchy import build_hierarchy
from organization.library import validate_library
from retrieval.bridge import (
    build_snapshots,
    create_freeze_manifest,
    export_queries,
    export_skills,
    load_skill_library,
    load_snapshots,
    verify_freeze_manifest,
)
from runtime.experiment import run_grid


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Frozen Skill organization experiment")
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-library")
    validate.add_argument("--library", default="skills/library")

    export = commands.add_parser("export-skills")
    export.add_argument("--library", default="skills/library")
    export.add_argument("--output", default="data/fcsr_exchange/skills_for_retrieval.jsonl")

    queries = commands.add_parser("export-queries")
    queries.add_argument("--input", required=True, help="JSON list of task_id + instruction/query")
    queries.add_argument("--output", default="data/fcsr_exchange/appworld_queries.jsonl")

    snapshots = commands.add_parser("build-snapshots")
    snapshots.add_argument("--records", required=True)
    snapshots.add_argument("--output", required=True)
    snapshots.add_argument("--provenance", required=True)
    snapshots.add_argument("--top-k", type=int, default=5)

    graph = commands.add_parser("build-graph")
    graph.add_argument("--library", default="skills/library")
    graph.add_argument(
        "--trajectory-orders",
        help="JSON list of successful/GT Train records with split and skill_ids",
    )
    graph.add_argument("--output", default="organization/global_graph.json")

    hierarchy = commands.add_parser("build-hierarchy")
    hierarchy.add_argument("--library", default="skills/library")
    hierarchy.add_argument("--output", default="organization/global_hierarchy.json")

    freeze = commands.add_parser("freeze")
    freeze.add_argument("--artifact", action="append", required=True, help="NAME=PATH")
    freeze.add_argument("--metadata", required=True)
    freeze.add_argument("--output", default="freeze_manifest.json")

    verify = commands.add_parser("verify-freeze")
    verify.add_argument("--manifest", default="freeze_manifest.json")

    analyze = commands.add_parser("analyze")
    analyze.add_argument("--runs", default="outputs/runs")
    analyze.add_argument("--output", default="outputs/results/summary.json")

    run = commands.add_parser("run")
    run.add_argument("--split", required=True)
    run.add_argument("--snapshots", required=True)
    run.add_argument("--library", default="skills/library")
    run.add_argument("--hierarchy", default="organization/global_hierarchy.json")
    run.add_argument("--graph", default="organization/global_graph.json")
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--task-limit", type=int)
    run.add_argument("--max-steps", type=int, default=30)
    run.add_argument("--seeds", default="42,43,44")
    run.add_argument("--conditions", default=",".join(CONDITIONS))
    run.add_argument("--output", default="outputs/runs")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "validate-library":
        result = validate_library(args.library)
    elif args.command == "export-skills":
        result = export_skills(args.library, args.output)
    elif args.command == "export-queries":
        result = {"count": export_queries(read_json(args.input), args.output)}
    elif args.command == "build-snapshots":
        result = build_snapshots(
            args.records, args.output, read_json(args.provenance), args.top_k
        )
    elif args.command == "build-graph":
        orders = read_json(args.trajectory_orders) if args.trajectory_orders else []
        result = build_global_graph(args.library, args.output, orders)
    elif args.command == "build-hierarchy":
        skill_ids = sorted(
            directory.name
            for directory in Path(args.library).iterdir()
            if directory.is_dir() and (directory / "SKILL.md").is_file()
        )
        result = build_hierarchy(skill_ids, args.library)
        write_json(args.output, result)
    elif args.command == "freeze":
        artifacts = dict(item.split("=", 1) for item in args.artifact)
        result = create_freeze_manifest(artifacts, read_json(args.metadata), args.output)
    elif args.command == "verify-freeze":
        result = verify_freeze_manifest(args.manifest)
    elif args.command == "analyze":
        result = analyze_runs(args.runs)
        write_json(args.output, result)
    else:
        result = _run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _run(args: argparse.Namespace) -> dict:
    model_config = {
        "base_url": os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        "api_key": os.environ.get("MODEL_API_KEY", "local"),
        "model_id": os.environ.get(
            "MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"
        ),
    }
    return run_grid(
        split=args.split,
        snapshots=load_snapshots(args.snapshots),
        library=load_skill_library(args.library),
        conditions=args.conditions.split(","),
        seeds=[int(value) for value in args.seeds.split(",")],
        model_config=model_config,
        output_root=args.output,
        hierarchy=read_json(args.hierarchy),
        graph=read_json(args.graph),
        max_steps=args.max_steps,
        workers=args.workers,
        task_limit=args.task_limit,
    )


if __name__ == "__main__":
    main()
