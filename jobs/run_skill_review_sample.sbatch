#!/bin/bash
#SBATCH --job-name=skill-review-v2
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --nodelist=GPU3
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=32
#SBATCH --mem=160G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/review-v2-%j.out
#SBATCH --error=logs/review-v2-%j.err

set -euo pipefail
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
FAMILIES="${FAMILIES:?Set FAMILIES to comma-separated family ids}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct}"
MODEL_PORT="${MODEL_PORT:-8000}"
SEEDS="${SEEDS:-42}"
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

log "Starting vLLM on $MODEL_PATH"
"$VLLM_BIN" serve "$MODEL_PATH" --host 127.0.0.1 --port "$MODEL_PORT" \
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len 32768 \
  --tensor-parallel-size 2 --gpu-memory-utilization 0.90 \
  --safetensors-load-strategy eager > "logs/vllm-review-$SLURM_JOB_ID.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

log "Waiting for vLLM health endpoint"
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

log "Running sampled skill review"
"$PYTHON_BIN" scripts/run_skill_review_sample.py \
  --library skills/library_v2 \
  --output outputs/skill_build_v2/review/sample_runs \
  --families "$FAMILIES" \
  --seeds "$SEEDS" \
  --max-steps 30 \
  --model-id "$MODEL_ID" \
  --base-url "$MODEL_BASE_URL"

log "Sampled review completed"
