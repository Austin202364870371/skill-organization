#!/usr/bin/env python3
"""Single command-line entry point for the complete experiment pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent import LocalModelClient
from appworld_runtime import audit_install
from contracts import contract_from_mapping, contract_prompt, parse_contract_response
from experiment import run_grid
from graph import build_candidate_graph, validate_graph
from analysis import analyze_runs
from retrieval_bridge import (
    build_snapshots, create_freeze_manifest, export_queries, export_skills,
    load_skill_library, load_snapshots, verify_freeze_manifest,
)
from schemas import CONDITIONS
from skill_generation import induction_prompt, parse_skill_markdown, write_skill_package
from trajectory import inspect_trajectory_tree, normalize_trajectory
from utils import read_json, write_json


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Skill organization experiment pipeline")
    commands = root.add_subparsers(dest="command", required=True)

    audit = commands.add_parser("audit-appworld")
    audit.add_argument("--root", required=True)
    audit.add_argument("--output-dir", default="outputs/audits")

    inspect_cmd = commands.add_parser("inspect-trajectories")
    inspect_cmd.add_argument("--root", required=True)
    inspect_cmd.add_argument("--output", default="outputs/audits/trajectory_schema.json")

    normalize = commands.add_parser("normalize-trajectory")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--task-id")
    normalize.add_argument("--output", required=True)

    export = commands.add_parser("export-skills")
    export.add_argument("--library", default="skills/library")
    export.add_argument("--output", default="data/fcsr_exchange/skills_for_retrieval.jsonl")

    queries = commands.add_parser("export-queries")
    queries.add_argument("--input", required=True, help="JSON list of task_id + instruction/query")
    queries.add_argument("--output", default="data/fcsr_exchange/appworld_queries.jsonl")

    snapshots = commands.add_parser("build-snapshots")
    snapshots.add_argument("--records", required=True)
    snapshots.add_argument("--output", required=True)
    snapshots.add_argument("--provenance", required=True, help="JSON provenance file")
    snapshots.add_argument("--top-k", type=int, default=5)

    graph = commands.add_parser("build-graph")
    graph.add_argument("--contracts", default="skills/library")
    graph.add_argument("--trajectory-orders", help="Optional JSON list of ordered skill-id lists")
    graph.add_argument("--output", default="organization/global_graph.json")

    hierarchy = commands.add_parser("build-hierarchy")
    hierarchy.add_argument("--contracts", default="skills/library")
    hierarchy.add_argument("--output", default="organization/global_hierarchy.json")

    generate = commands.add_parser("generate-skill")
    generate.add_argument("--task", required=True, help="JSON file with task_id, split, instruction")
    generate.add_argument("--reference", required=True)
    generate.add_argument("--library", default="skills/library")
    generate.add_argument("--seed", type=int, default=42)

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
    if args.command == "audit-appworld":
        result = audit_install(args.root, args.output_dir)
    elif args.command == "inspect-trajectories":
        result = inspect_trajectory_tree(args.root, args.output)
    elif args.command == "normalize-trajectory":
        result = normalize_trajectory(args.input, args.task_id)
        write_json(args.output, result)
    elif args.command == "export-skills":
        result = export_skills(args.library, args.output)
    elif args.command == "export-queries":
        result = {"count": export_queries(read_json(args.input), args.output)}
    elif args.command == "build-snapshots":
        result = build_snapshots(args.records, args.output, read_json(args.provenance), args.top_k)
    elif args.command == "build-graph":
        contracts = _load_contracts(args.contracts)
        orders = read_json(args.trajectory_orders) if args.trajectory_orders else []
        result = build_candidate_graph(contracts, orders)
        validate_graph(result)
        write_json(args.output, result)
    elif args.command == "build-hierarchy":
        result = _build_hierarchy(_load_contracts(args.contracts))
        write_json(args.output, result)
    elif args.command == "generate-skill":
        result = _generate_skill(args)
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


def _load_contracts(root: str | Path) -> list[Any]:
    return [contract_from_mapping(read_json(path)) for path in sorted(Path(root).glob("*/contract.json"))]


def _build_hierarchy(contracts: list[Any]) -> dict[str, Any]:
    paths = {}
    for contract in contracts:
        app = contract.apps[0] if contract.apps else "General"
        paths[contract.skill_id] = [contract.domain, app, contract.capability]
    return {"schema_version": "skill_hierarchy_v1", "paths": paths}


def _local_model() -> LocalModelClient:
    return LocalModelClient(
        base_url=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key=os.environ.get("MODEL_API_KEY", "local"),
        model_id=os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    )


def _generate_skill(args: argparse.Namespace) -> dict[str, Any]:
    task, reference = read_json(args.task), read_json(args.reference)
    if task.get("split") != "train":
        raise ValueError("generate-skill accepts Train tasks only")
    model = _local_model()
    reply = model.complete([{"role": "user", "content": induction_prompt(task["instruction"], reference)}], args.seed)
    skill_id = str(task["task_id"]).replace("_", "-")
    skill = parse_skill_markdown(skill_id, reply.text, {"source_task": task["task_id"]})
    contract_reply = model.complete([{"role": "user", "content": contract_prompt(skill_id, skill.body)}], args.seed)
    contract = parse_contract_response(contract_reply.text, skill_id)
    destination = write_skill_package(
        args.library, skill, contract,
        {"source_task": task["task_id"], "generation_seed": args.seed, "validation_status": "pending"},
        split="train",
    )
    return {"skill_id": skill_id, "path": str(destination), "validation_status": "pending"}


def _run(args: argparse.Namespace) -> dict[str, Any]:
    model_config = {
        "base_url": os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8000/v1"),
        "api_key": os.environ.get("MODEL_API_KEY", "local"),
        "model_id": os.environ.get("MODEL_ID", "Qwen/Qwen3-Coder-30B-A3B-Instruct"),
    }
    return run_grid(
        split=args.split, snapshots=load_snapshots(args.snapshots),
        library=load_skill_library(args.library), conditions=args.conditions.split(","),
        seeds=[int(value) for value in args.seeds.split(",")], model_config=model_config,
        output_root=args.output, hierarchy=read_json(args.hierarchy), graph=read_json(args.graph),
        max_steps=args.max_steps, workers=args.workers, task_limit=args.task_limit,
    )


if __name__ == "__main__":
    main()

