#!/bin/bash
#SBATCH --job-name=skill-org-bc
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --nodelist=GPU2,GPU3
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=12
#SBATCH --mem=96G
#SBATCH --time=1-00:00:00
#SBATCH --array=0-2%1
#SBATCH --output=logs/validate-skills-%A_%a.out
#SBATCH --error=logs/validate-skills-%A_%a.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct}"
MODEL_PORT="${MODEL_PORT:-8000}"
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
mkdir -p "$PIP_CACHE_DIR" "$HF_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" \
  "$VLLM_CACHE_ROOT" "$VLLM_CONFIG_ROOT" "$CUDA_CACHE_PATH" "$NUMBA_CACHE_DIR" "$TMPDIR" logs
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
export APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
export MODEL_BASE_URL="http://127.0.0.1:$MODEL_PORT/v1"
export MODEL_API_KEY=local OPENAI_API_KEY=local MODEL_SERVER_URL="$MODEL_BASE_URL"
export MODEL_ID=Qwen/Qwen3-Coder-30B-A3B-Instruct MODEL_PORT
export PYTHONWARNINGS=ignore
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY="127.0.0.1,localhost" no_proxy="127.0.0.1,localhost"

vllm serve "$MODEL_PATH" --host 127.0.0.1 --port "$MODEL_PORT" \
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len 32768 \
  --tensor-parallel-size 2 --gpu-memory-utilization 0.90 > "logs/vllm-$SLURM_ARRAY_JOB_ID-$SLURM_ARRAY_TASK_ID.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT
python - <<'PY'
import os
import time
import urllib.request
for _ in range(180):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{os.environ['MODEL_PORT']}/health", timeout=2)
        break
    except Exception:
        time.sleep(5)
else:
    raise SystemExit("local vLLM server did not become healthy")
PY
NUM_SHARDS="${NUM_SHARDS_OVERRIDE:-$SLURM_ARRAY_TASK_COUNT}"
python scripts/validate_families.py \
  --shard-index "$SLURM_ARRAY_TASK_ID" --num-shards "$NUM_SHARDS"
