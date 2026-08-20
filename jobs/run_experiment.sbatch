#!/bin/bash
#SBATCH --job-name=skill-org-run
#SBATCH --qos=fast
#SBATCH --nodes=1
#SBATCH --nodelist=GPU2,GPU3
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=160G
#SBATCH --time=06:00:00
#SBATCH --output=logs/run-%j.out
#SBATCH --error=logs/run-%j.err

set -euo pipefail
log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
SPLIT="${SPLIT:?Set SPLIT to dev, test_normal, or test_challenge}"
SNAPSHOTS="${SNAPSHOTS:?Set SNAPSHOTS to the frozen split snapshot JSONL}"
FREEZE_MANIFEST="${FREEZE_MANIFEST:-$PROJECT_DIR/freeze_manifest.json}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct}"
MODEL_PORT="${MODEL_PORT:-8000}"
WORKERS="${WORKERS:-4}"
SEEDS="${SEEDS:-42,43,44}"
CONDITIONS="${CONDITIONS:-No-Skill,Flat-NoPD,Flat-PD,Hierarchy-PD,Graph-PD}"
TASK_LIMIT="${TASK_LIMIT:-}"
TASK_IDS="${TASK_IDS:-}"
RUN_OUTPUT="${RUN_OUTPUT:-$PROJECT_DIR/outputs/runs}"
PYTHON_BIN="$PROJECT_DIR/env/bin/python"
VLLM_BIN="$PROJECT_DIR/env/bin/vllm"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export PIP_CACHE_DIR="$PROJECT_DIR/.cache/pip"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export VLLM_CACHE_ROOT="$PROJECT_DIR/.cache/vllm"
export VLLM_CONFIG_ROOT="$PROJECT_DIR/.cache/vllm-config"
export CUDA_CACHE_PATH="$PROJECT_DIR/.cache/cuda"
export NUMBA_CACHE_DIR="$PROJECT_DIR/.cache/numba"
export TMPDIR="$PROJECT_DIR/.cache/tmp"
export PYTHONUNBUFFERED=1
mkdir -p "$PIP_CACHE_DIR" "$HF_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" \
  "$VLLM_CACHE_ROOT" "$VLLM_CONFIG_ROOT" "$CUDA_CACHE_PATH" "$NUMBA_CACHE_DIR" "$TMPDIR"
mkdir -p logs outputs/runs .cache/huggingface
[[ -x "$PYTHON_BIN" ]] || { echo "Missing project Python: $PYTHON_BIN" >&2; exit 1; }
[[ -x "$VLLM_BIN" ]] || { echo "Missing project vLLM: $VLLM_BIN" >&2; exit 1; }
export APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export MODEL_BASE_URL="http://127.0.0.1:$MODEL_PORT/v1" MODEL_API_KEY=local OPENAI_API_KEY=local
export MODEL_SERVER_URL="$MODEL_BASE_URL"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY="127.0.0.1,localhost" no_proxy="127.0.0.1,localhost"
export MODEL_ID=Qwen/Qwen3-Coder-30B-A3B-Instruct

log "Job $SLURM_JOB_ID started on $(hostname)"
log "Pilot configuration: split=$SPLIT seeds=$SEEDS task_limit=${TASK_LIMIT:-all}"
log "Conditions: $CONDITIONS"
log "Snapshots: $SNAPSHOTS"
log "Freeze manifest: $FREEZE_MANIFEST"
"$PYTHON_BIN" scripts/main.py verify-freeze --manifest "$FREEZE_MANIFEST"
"$PYTHON_BIN" scripts/verify_frozen_input.py --manifest "$FREEZE_MANIFEST" --path "$SNAPSHOTS"
"$PYTHON_BIN" scripts/verify_library.py --library skills/library --manifest skills/manifest.json
log "Frozen inputs verified"

"$VLLM_BIN" serve "$MODEL_PATH" --host 127.0.0.1 --port "$MODEL_PORT" \
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len 32768 \
  --tensor-parallel-size 2 --gpu-memory-utilization 0.90 \
  --safetensors-load-strategy eager > "logs/vllm-$SLURM_JOB_ID.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT
log "vLLM started with PID $SERVER_PID; waiting for health endpoint"

"$PYTHON_BIN" - <<PY
import os, time, urllib.request
for _ in range(540):
    try:
        os.kill($SERVER_PID, 0)
    except ProcessLookupError:
        raise SystemExit("local vLLM server exited before becoming healthy")
    try:
        urllib.request.urlopen("http://127.0.0.1:$MODEL_PORT/health", timeout=2)
        break
    except Exception:
        time.sleep(5)
else:
    raise SystemExit("local vLLM server did not become healthy")
PY

log "vLLM is healthy; starting AppWorld runs"
RUN_ARGS=(
  scripts/main.py run
  --split "$SPLIT"
  --snapshots "$SNAPSHOTS"
  --workers "$WORKERS"
  --seeds "$SEEDS"
  --conditions "$CONDITIONS"
  --output "$RUN_OUTPUT"
)
[[ -z "$TASK_LIMIT" ]] || RUN_ARGS+=(--task-limit "$TASK_LIMIT")
[[ -z "$TASK_IDS" ]] || RUN_ARGS+=(--task-ids "$TASK_IDS")
"$PYTHON_BIN" "${RUN_ARGS[@]}"
log "AppWorld pilot completed successfully"
