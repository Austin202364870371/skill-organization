# Skill Organization

面向 AppWorld 的可审计 Skill 组织实验。项目固定检索结果、Agent、模型和环境，比较：

```text
No-Skill
Flat-NoPD
Flat-PD
Hierarchy-PD
Graph-PD
```

正式 Skill 条件对每个任务使用相同的 FCSR Top-5 snapshot。Graph-PD 只展示 Top-5 的 induced subgraph，不做 PPR、图扩展、补点、自动规划或局部修复。

## 集群约束

- 登录节点仅用于代码、检查、提交和短测试。
- 正式预处理、推理和评测全部通过 Slurm。
- AppWorld 使用项目本地 `./env`，FCSR 继续使用其冻结环境。
- Qwen3-Coder-30B-A3B-Instruct 仅在 GPU4 的单张 H200 上、在作业生命周期内本地部署。
- `.env`、模型、数据、缓存和正式输出不进入 Git。
- 安装、下载和提交作业前必须人工检查命令。

## 代码入口

所有核心模块直接位于 `src/`，命令统一由 `scripts/main.py` 提供：

```bash
python scripts/main.py --help
python scripts/main.py audit-appworld --help
python scripts/main.py inspect-trajectories --help
python scripts/main.py generate-skill --help
python scripts/main.py build-graph --help
python scripts/main.py build-snapshots --help
python scripts/main.py freeze --help
python scripts/main.py run --help
python scripts/main.py analyze --help
```

## 执行顺序

### 0. 人工审查并创建环境

项目已固定 AppWorld commit 和兼容依赖版本；人工复核后提交 CPU setup 作业：

```bash
cd /data-nfs/gpu3/u13256401368/skill-organization
sbatch jobs/setup_appworld.sbatch
```

下载任务数据和官方轨迹：

```bash
sbatch jobs/download_appworld.sbatch
```

该作业同时运行 AppWorld verify 并写入 `outputs/audits/`。

### 1. 本地模型 smoke test

模型权重只保留一份在 `models/Qwen3-Coder-30B-A3B-Instruct/`。确认权重存在后：

```bash
sbatch jobs/smoke_appworld.sbatch
```

该作业申请 GPU4 单张 H200，启动仅绑定 loopback 的 vLLM，完成一个 No-Skill Dev task 后自动关闭服务。

### 2. Trajectory 与 Skill

先检查官方输出，绝不假定 schema：

```bash
python scripts/main.py inspect-trajectories \
  --root data/appworld/experiments/outputs \
  --output outputs/audits/trajectory_schema.json
```

将一条真实轨迹规范化后，调用本地模型生成 Skill package。新 Skill 的 validation 状态初始为 `pending`；只有 deduction run 通过 AppWorld evaluator 后，才允许在 manifest 中标为 validated 并进入冻结 Library。

Skill generation 入口会拒绝任何非 Train task。

### 3. Organization

```bash
python scripts/main.py build-hierarchy
python scripts/main.py build-graph
```

Graph 的 dependency 来自 output/effect 与 input/precondition 的确定性匹配，workflow 来自 Train trajectory 顺序。所有 dependency/workflow edges 必须无环且保留 evidence。

### 4. Frozen FCSR snapshots

导出 JSONL 后提交冻结 FCSR 推理：

```bash
python scripts/main.py export-skills
python scripts/main.py export-queries --input data/tasks/dev.json
sbatch jobs/fcsr_snapshots.sbatch
```

然后把 reranker records 转为带 SHA-256 的 Top-5 snapshots：

```bash
python scripts/main.py build-snapshots \
  --records data/fcsr_exchange/inference/rerank_records.jsonl \
  --provenance data/fcsr_exchange/provenance.json \
  --output data/retrieval_snapshots/dev.jsonl
```

### 5. Freeze 与正式运行

`freeze` 对模型 revision、配置、Library manifest、Hierarchy、Graph 和所有 split snapshots 建立内容 hash。正式作业首先执行 `verify-freeze`，任一文件变化都会中止。

```bash
sbatch --export=ALL,SPLIT=test_normal,SNAPSHOTS=$PWD/data/retrieval_snapshots/test_normal.jsonl jobs/run_experiment.sbatch
sbatch --export=ALL,SPLIT=test_challenge,SNAPSHOTS=$PWD/data/retrieval_snapshots/test_challenge.jsonl jobs/run_experiment.sbatch
```

不要同时提交大量相似作业；一个 split 作业内部使用 4 个隔离 worker，共享单张 H200 上的本地模型。

## 八个正式指标

1. TGC
2. SGC
3. Success Rate
4. Total Tokens
5. Execution Steps
6. Wall-clock Time
7. Skill Utilization Rate
8. Unique Skills Loaded

Token Reduction、Skill Lift 和 Step Reduction仅作为上述指标的条件间差值，不增加主指标数。

## 本地轻量验证

以下命令不加载模型或 AppWorld：

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src scripts
bash -n jobs/*.sbatch
```

