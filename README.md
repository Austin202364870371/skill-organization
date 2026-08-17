# Skill Organization

面向 AppWorld 的可审计 Skill 组织实验。项目固定 Skill Library、检索结果、Agent、模型和环境，比较：

- No-Skill
- Flat-NoPD
- Flat-PD
- Hierarchy-PD
- Graph-PD

四个 Skill 条件对同一任务使用相同的 FCSR Top-5 snapshot。Graph-PD 只展示 Top-5 induced subgraph，不执行图扩展、自动补点或图规划。

## 最终实验资产

- Library：`skills/library/`，共 45 个 Train-grounded Skills
- Manifest：`skills/manifest.json`
- Hierarchy：`organization/global_hierarchy.json`
- Graph：`organization/global_graph.json`
- 构建摘要：`outputs/audits/skill_library_build_summary.json`

每个 Skill package 仅包含 `SKILL.md`、`metadata.json` 和 `references/`。本阶段不使用 Contract。

## 源码结构

```text
src/
├── common/         # schema、文件与 hash 工具
├── runtime/        # Agent、AppWorld 和实验执行
├── organization/   # Library、Loader、视图、Hierarchy、Graph
├── retrieval/      # FCSR JSONL 交换、snapshot 与冻结
└── evaluation/     # 九项指标和统计分析
```

`scripts/main.py` 只保留主实验所需命令：

```bash
python scripts/main.py --help
python scripts/main.py validate-library
python scripts/main.py build-hierarchy
python scripts/main.py build-graph
python scripts/main.py export-skills
python scripts/main.py build-snapshots --help
python scripts/main.py freeze --help
python scripts/main.py run --help
python scripts/main.py analyze --help
```

Skill 生成、候选 refinement 和 deduction validation 已作为一次性预处理结束，其脚本与大体积中间结果不属于正式实验代码。

## 集群约束

- 登录节点仅用于代码检查、轻量验证和提交作业。
- 推理与正式评测通过 Slurm。
- AppWorld 使用项目本地 `./env`。
- Qwen3-Coder-30B-A3B-Instruct 使用单节点两张 L40、Tensor Parallel=2，本地 vLLM 只绑定 loopback。
- 模型、数据、缓存、日志和正式运行输出不进入 Git。

## 正式流程

1. 验证 Library 和 manifest。
2. 导出 Skill 与任务查询 JSONL。
3. 使用冻结 FCSR 生成相同的 Top-5 snapshots。
4. 冻结模型 revision、配置、Library、Hierarchy、Graph 与 snapshots。
5. 对五种条件执行配对实验。
6. 使用官方 AppWorld evaluator 和本项目九项指标汇总。

```bash
PYTHONPATH=src ./env/bin/python scripts/validate_library.py --library skills/library
PYTHONPATH=src ./env/bin/python scripts/verify_library.py \
  --library skills/library --manifest skills/manifest.json

PYTHONPATH=src ./env/bin/python scripts/main.py export-skills
PYTHONPATH=src ./env/bin/python scripts/main.py export-queries \
  --input data/tasks/dev.json
sbatch jobs/fcsr_snapshots.sbatch
```

正式运行前必须生成并验证 `freeze_manifest.json`。任一冻结输入 hash 改变都应阻止作业启动。

## 九个正式指标

1. TGC
2. SGC
3. Success Rate
4. Requirement Completion Rate
5. Total Tokens
6. Execution Steps
7. Wall-clock Time
8. Skill Utilization Rate
9. Unique Skills Loaded

Token Reduction、Skill Lift 和 Step Reduction是条件间派生对比，不增加主指标数量。

## 轻量验证

```bash
PYTHONPATH=src ./env/bin/python -m unittest discover -s tests -v
./env/bin/python -m compileall -q src scripts
bash -n jobs/*.sbatch
```
