#!/bin/bash
#SBATCH --job-name=skill-org-data
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=logs/download-%j.out
#SBATCH --error=logs/download-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
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
mkdir -p logs "$APPWORLD_ROOT" outputs/audits
export APPWORLD_ROOT HF_HOME="$PROJECT_DIR/.cache/huggingface"

python -m appworld.cli download data --root "$APPWORLD_ROOT"
python -m appworld.cli download experiment-outputs --root "$APPWORLD_ROOT"
python -m appworld.cli verify tests --root "$APPWORLD_ROOT"
python -m appworld.cli verify tasks --root "$APPWORLD_ROOT"
python scripts/main.py audit-appworld --root "$APPWORLD_ROOT" --output-dir outputs/audits
python scripts/audit_agent.py
OUTPUT_ROOT="$APPWORLD_ROOT/experiments/outputs"
if [[ -d "$OUTPUT_ROOT" ]]; then python scripts/main.py inspect-trajectories --root "$OUTPUT_ROOT" --output outputs/audits/trajectory_schema.json; fi

