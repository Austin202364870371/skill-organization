#!/bin/bash
#SBATCH --job-name=skill-org-run
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --nodelist=GPU4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=32
#SBATCH --mem=160G
#SBATCH --time=3-00:00:00
#SBATCH --output=logs/run-%j.out
#SBATCH --error=logs/run-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
SPLIT="${SPLIT:?Set SPLIT to dev, test_normal, or test_challenge}"
SNAPSHOTS="${SNAPSHOTS:?Set SNAPSHOTS to the frozen split snapshot JSONL}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct}"
MODEL_PORT="${MODEL_PORT:-8000}"
WORKERS="${WORKERS:-4}"
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
  "$VLLM_CACHE_ROOT" "$VLLM_CONFIG_ROOT" "$CUDA_CACHE_PATH" "$NUMBA_CACHE_DIR" "$TMPDIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
mkdir -p logs outputs/runs .cache/huggingface
export APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export MODEL_BASE_URL="http://127.0.0.1:$MODEL_PORT/v1" MODEL_API_KEY=local
export MODEL_ID=Qwen/Qwen3-Coder-30B-A3B-Instruct

python scripts/main.py verify-freeze --manifest freeze_manifest.json
python scripts/verify_frozen_input.py --manifest freeze_manifest.json --path "$SNAPSHOTS"
python scripts/verify_library.py --library skills/library --manifest skills/manifest.json
vllm serve "$MODEL_PATH" --host 127.0.0.1 --port "$MODEL_PORT" \
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.90 > "logs/vllm-$SLURM_JOB_ID.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT

python - <<PY
import time, urllib.request
for _ in range(180):
    try:
        urllib.request.urlopen("http://127.0.0.1:$MODEL_PORT/health", timeout=2)
        break
    except Exception:
        time.sleep(5)
else:
    raise SystemExit("local vLLM server did not become healthy")
PY

python scripts/main.py run --split "$SPLIT" --snapshots "$SNAPSHOTS" --workers "$WORKERS"

