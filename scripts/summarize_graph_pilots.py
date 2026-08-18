#!/usr/bin/env python3
"""Create reproducible JSON and Markdown summaries for the Graph-PD v2 pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
import sys

sys.path.insert(0, str(SRC))

from reporting.analysis import analyze_runs  # noqa: E402
from reporting.metrics import METRIC_NAMES, scenario_outcomes, summarize  # noqa: E402


CONDITIONS = ("No-Skill", "Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD")
EXPERIMENTS = {
    "smoke": ("outputs/runs/smoke_graph_v2", 1),
    "original5": ("outputs/runs/pilot_graph_v2_original5", 5),
    "stratified9": ("outputs/runs/pilot_graph_v2_stratified", 9),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "outputs/results/graph_pd_v2_pilot_summary.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=ROOT / "outputs/results/graph_pd_v2_pilot_report.md",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    return parser.parse_args()


def load_records(path: Path) -> tuple[list[dict[str, Any]], str]:
    files = sorted(path.rglob("*.json"))
    digest = hashlib.sha256()
    records = []
    for file in files:
        payload = file.read_bytes()
        digest.update(file.relative_to(ROOT).as_posix().encode())
        digest.update(payload)
        records.append(json.loads(payload))
    return records, digest.hexdigest()


def validate_records(records: list[dict[str, Any]], expected_tasks: int) -> dict[str, Any]:
    tasks = sorted({str(record["task_id"]) for record in records})
    seeds = sorted({int(record["seed"]) for record in records})
    missing = []
    duplicates = []
    counts: dict[tuple[str, int, str], int] = defaultdict(int)
    for record in records:
        counts[(str(record["task_id"]), int(record["seed"]), str(record["condition"]))] += 1
    for task in tasks:
        for seed in seeds:
            for condition in CONDITIONS:
                count = counts[(task, seed, condition)]
                if count == 0:
                    missing.append([task, seed, condition])
                elif count > 1:
                    duplicates.append([task, seed, condition, count])
    expected_records = expected_tasks * len(seeds) * len(CONDITIONS)
    return {
        "valid": (
            len(tasks) == expected_tasks
            and len(records) == expected_records
            and not missing
            and not duplicates
            and not any(record.get("error") for record in records)
        ),
        "record_count": len(records),
        "expected_record_count": expected_records,
        "task_count": len(tasks),
        "expected_task_count": expected_tasks,
        "tasks": tasks,
        "seeds": seeds,
        "conditions": sorted({str(record["condition"]) for record in records}),
        "missing_cells": missing,
        "duplicate_cells": duplicates,
        "runtime_error_count": sum(bool(record.get("error")) for record in records),
        "max_steps_reached_count": sum(bool(record.get("max_steps_reached")) for record in records),
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_condition[str(record["condition"])].append(record)
    summaries = {condition: summarize(by_condition[condition]) for condition in CONDITIONS}
    outcomes = scenario_outcomes(records)
    return {
        "summaries": summaries,
        "complete_scenario_count_per_condition": {
            condition: sum(key[1] == condition for key in outcomes) for condition in CONDITIONS
        },
        "successful_runs": sorted(
            {
                f"{record['task_id']}::{record['condition']}"
                for record in records
                if record.get("success")
            }
        ),
    }


def combined_pilot(records_by_name: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    records = records_by_name["original5"] + records_by_name["stratified9"]
    return {
        "note": "Descriptive aggregation of the two pilots; smoke is excluded.",
        "validation": validate_records(records, expected_tasks=14),
        **summarize_records(records),
    }


def pct(value: float) -> str:
    return "—" if not math.isfinite(value) else f"{100 * value:.1f}%"


def number(value: float, digits: int = 1) -> str:
    return "—" if not math.isfinite(value) else f"{value:.{digits}f}"


def json_ready(value: Any) -> Any:
    """Replace non-finite floats so the output is strict RFC-compliant JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value


def mean(summary: dict[str, Any], metric: str) -> float:
    return float(summary[metric]["mean"])


def outcome_table(title: str, experiment: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", ""]
    valid = experiment["validation"]
    lines.append(
        f"完整性：{valid['record_count']}/{valid['expected_record_count']} 条结果，"
        f"{valid['task_count']} 个任务，seed={valid['seeds']}，"
        f"运行错误 {valid['runtime_error_count']} 条，触及 max steps {valid['max_steps_reached_count']} 条。"
    )
    lines.extend(
        [
            "",
            "| Condition | TGC / Success | RCR | SGC | Tokens mean / median | Steps mean | Time mean (s) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    summaries = experiment["summaries"]
    for condition in CONDITIONS:
        summary = summaries[condition]
        lines.append(
            "| "
            + " | ".join(
                [
                    condition,
                    pct(mean(summary, "tgc")),
                    pct(mean(summary, "requirement_completion_rate")),
                    pct(mean(summary, "sgc")),
                    f"{number(mean(summary, 'total_tokens'), 0)} / "
                    f"{number(float(summary['total_tokens']['median']), 0)}",
                    number(mean(summary, "execution_steps")),
                    number(mean(summary, "wall_clock_time")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Skill condition | Utilization | Unique loaded mean |",
            "|---|---:|---:|",
        ]
    )
    for condition in ("Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD"):
        summary = summaries[condition]
        lines.append(
            f"| {condition} | {pct(mean(summary, 'skill_utilization_rate'))} | "
            f"{number(mean(summary, 'unique_skills_loaded'))} |"
        )
    return lines + [""]


def comparison_table(experiment: dict[str, Any]) -> list[str]:
    summaries = experiment["summaries"]
    no_skill = summaries["No-Skill"]
    flat_nopd = summaries["Flat-NoPD"]
    lines = [
        "| Condition | TGC lift vs No-Skill | RCR lift vs No-Skill | Token change vs Flat-NoPD | Step change vs Flat-NoPD |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition in ("Flat-NoPD", "Flat-PD", "Hierarchy-PD", "Graph-PD"):
        current = summaries[condition]
        tgc_lift = mean(current, "tgc") - mean(no_skill, "tgc")
        rcr_lift = mean(current, "requirement_completion_rate") - mean(
            no_skill, "requirement_completion_rate"
        )
        token_change = mean(current, "total_tokens") / mean(flat_nopd, "total_tokens") - 1
        step_change = mean(current, "execution_steps") / mean(flat_nopd, "execution_steps") - 1
        lines.append(
            f"| {condition} | {tgc_lift * 100:+.1f} pp | {rcr_lift * 100:+.1f} pp | "
            f"{token_change * 100:+.1f}% | {step_change * 100:+.1f}% |"
        )
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    smoke = payload["experiments"]["smoke"]
    original = payload["experiments"]["original5"]
    stratified = payload["experiments"]["stratified9"]
    combined = payload["combined_pilot"]
    lines = [
        "# Graph-PD v2 Pilot 汇总",
        "",
        f"生成时间：{payload['generated_at']}。",
        "",
        "三个作业的结果文件均完整，且没有运行级错误。Smoke 仅用于链路验收；由于其任务在原 5 任务 Pilot 中重复，未计入合并结果。",
        "",
        "> TGC 与 Success Rate 在当前实现中均为任务级二值成功，数值相同；RCR 是 evaluator requirements 的平均完成比例。SGC 仅对恰好包含 3 个 task variants 的完整 scenario 计算。",
        "",
        "## Smoke 验收",
        "",
        f"5/5 条条件结果完整，成功条件：{', '.join(smoke['successful_runs']) or '无'}。这证明新 Graph-PD 链路可执行，但单任务不能用于效果结论。",
        "",
    ]
    lines += outcome_table("原 5 任务 Pilot", original)
    lines += ["### 相对变化", ""] + comparison_table(original) + [""]
    lines += outcome_table("分层 9 任务 Pilot", stratified)
    lines += ["### 相对变化", ""] + comparison_table(stratified) + [""]
    lines += outcome_table("合并描述性结果（14 tasks，不含 smoke）", combined)
    lines += [
        "## 结果解读",
        "",
        "1. **Hierarchy-PD 当前最稳定。** 原 5 任务中成功率 40.0%，分层 9 任务中为 22.2%；两个 Pilot 都没有显示层级组织比无 Skill 更差。合并 14 任务后它也是成功率最高的条件。",
        "2. **Graph-PD 相比修复前已有改善，但还没有稳定胜出。** 原 5 任务仍为 0/5；分层 9 任务达到 1/9，并取得该组最高 RCR（68.7%），说明真实证据图至少没有持续制造错误先后关系，但其任务级收益仍不稳定。",
        "3. **Graph-PD 的主要问题已从图语义错误转为成本与选用效率。** 原 5 任务平均 139,212 tokens、16.0 steps，分别比 Flat-NoPD 高 101.3% 和 66.7%；分层 9 任务成本差距缩小到 +6.5% tokens 和 +23.4% steps，但仍未形成效率优势。",
        "4. **Flat-PD 表现偏弱。** 两轮 Pilot 都是 0 个成功任务，说明仅暴露摘要、再由模型决定加载，在当前模型和提示下可能导致加载不足或选错 Skill；这不是 Graph 独有问题。",
        "5. **SGC 暂时没有区分度。** 所有条件均为 0；原 5 任务只有 1 个完整 scenario，分层 Pilot 也只有 3 个，因此现阶段应主要看任务级 TGC、RCR 与成本，不能据此判断组织方式无效。",
        "6. **本轮只能作为机制验证和趋势判断。** 每个 task 只有 seed 42，且样本分别只有 5 和 9 个任务；任务差异远大于条件差异，不应把当前排序写成统计显著结论。",
        "7. **预注册配对比较均未达到显著。** 两轮 Pilot 的 Holm 校正 p 值均不低于 0.1875；当前观察到的是效应方向，不是可推广的统计证据。",
        "",
        "## 下一步建议",
        "",
        "- 先做任务级错误审计，重点比较 `6c2c621_1`（Graph-PD 成功）与原 5 任务中 Graph-PD 的失败路径，确认收益来自正确关系展示而不是随机采样。",
        "- 检查 PD 条件的加载触发率。分层 9 任务中 Graph-PD 平均只加载 0.44 个 Skill，Library 有用并不等于模型真正读取了正文。",
        "- 在冻结图和提示词后，用更多 Dev tasks 或至少增加 seeds 再决定是否进入 Test；不要根据这 14 个任务继续针对性修改 Skill 正文。",
        "- 正式报告中保留九项指标，但 TGC 与 Success Rate 数值重复这一点必须明确说明；后续可在论文表中并列遵循预注册，同时避免重复解读。",
        "",
        "## 可复现性",
        "",
        "完整数值、四组预注册配对比较、bootstrap CI、置换检验和输入目录 hash 见 `graph_pd_v2_pilot_summary.json`。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    records_by_name: dict[str, list[dict[str, Any]]] = {}
    experiments: dict[str, Any] = {}
    for name, (relative_path, expected_tasks) in EXPERIMENTS.items():
        path = ROOT / relative_path
        records, digest = load_records(path)
        records_by_name[name] = records
        analysis = analyze_runs(path, bootstrap_samples=args.bootstrap_samples)
        experiments[name] = {
            "source": relative_path,
            "input_sha256": digest,
            "validation": validate_records(records, expected_tasks),
            **summarize_records(records),
            "paired_analysis": analysis["comparisons"].get("dev", []),
        }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metric_names": list(METRIC_NAMES),
        "experiments": experiments,
        "combined_pilot": combined_pilot(records_by_name),
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload))
    args.json_output.write_text(
        json.dumps(json_ready(payload), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    print(args.json_output)
    print(args.markdown_output)


if __name__ == "__main__":
    main()
