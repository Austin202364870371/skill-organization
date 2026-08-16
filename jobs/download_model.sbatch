#!/bin/bash
#SBATCH --job-name=skill-org-model
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=logs/model-%j.out
#SBATCH --error=logs/model-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
MODEL_REF="${MODEL_REF:-b2cff646eb4bb1d68355c01b18ae02e7cf42d120}"
MODEL_DIR="$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export PIP_CACHE_DIR="$PROJECT_DIR/.cache/pip"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HUB_DISABLE_XET=1
export HF_HUB_DOWNLOAD_TIMEOUT=600
export HF_HUB_ETAG_TIMEOUT=30
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
mkdir -p logs models "$MODEL_DIR" .cache/huggingface
export HF_HOME="$PROJECT_DIR/.cache/huggingface" MODEL_REF MODEL_DIR
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
df -h "$PROJECT_DIR"
python - <<PY
import os
import time

from huggingface_hub import snapshot_download

last_error = None
for attempt in range(1, 21):
    print(f"Snapshot download attempt {attempt}/20", flush=True)
    try:
        snapshot_download(
            repo_id="Qwen/Qwen3-Coder-30B-A3B-Instruct",
            revision=os.environ["MODEL_REF"],
            local_dir=os.environ["MODEL_DIR"],
            max_workers=2,
        )
        break
    except Exception as exc:
        last_error = exc
        print(f"Attempt {attempt} failed: {exc!r}", flush=True)
        if attempt < 20:
            time.sleep(15)
else:
    raise RuntimeError("Qwen snapshot download failed after 20 attempts") from last_error
PY
python scripts/record_model_metadata.py --model "$MODEL_DIR" --revision "$MODEL_REF" --output models/model_metadata.json
