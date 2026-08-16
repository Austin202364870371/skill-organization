#!/bin/bash
#SBATCH --job-name=skill-org-setup
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/setup-%j.out
#SBATCH --error=logs/setup-%j.err

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
APPWORLD_REF="${APPWORLD_REF:-a072b7a86e7c1d5b1d7175659d750ebb9b79f10a}"
VLLM_VERSION="${VLLM_VERSION:-0.11.2}"
OPENAI_VERSION="${OPENAI_VERSION:-1.99.8}"
LITELLM_VERSION="${LITELLM_VERSION:-1.78.2}"
TRANSFORMERS_VERSION="${TRANSFORMERS_VERSION:-4.56.2}"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export PIP_CACHE_DIR="$PROJECT_DIR/.cache/pip"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export APPWORLD_CACHE="$PROJECT_DIR/.cache/appworld"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export VLLM_CACHE_ROOT="$PROJECT_DIR/.cache/vllm"
export VLLM_CONFIG_ROOT="$PROJECT_DIR/.cache/vllm-config"
export CUDA_CACHE_PATH="$PROJECT_DIR/.cache/cuda"
export NUMBA_CACHE_DIR="$PROJECT_DIR/.cache/numba"
export TMPDIR="$PROJECT_DIR/.cache/tmp"
export CONDA_PKGS_DIRS="$PROJECT_DIR/.cache/conda-pkgs"
mkdir -p logs outputs/audits "$PIP_CACHE_DIR" "$HF_HOME" "$APPWORLD_CACHE" "$TORCH_HOME" \
  "$TRITON_CACHE_DIR" "$VLLM_CACHE_ROOT" "$VLLM_CONFIG_ROOT" "$CUDA_CACHE_PATH" \
  "$NUMBA_CACHE_DIR" "$TMPDIR" "$CONDA_PKGS_DIRS"

if [[ ! -x env/bin/python ]]; then
  conda create -p "$PROJECT_DIR/env" python=3.11 -y
fi
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"

export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export GIT_CONFIG_GLOBAL="$PROJECT_DIR/.gitconfig-lfs"
git lfs install --force
python -m pip install -e '.[test]'
python -m pip install \
  "appworld @ git+https://github.com/StonyBrookNLP/appworld.git@${APPWORLD_REF}" \
  "appworld-agents[simplified] @ git+https://github.com/StonyBrookNLP/appworld.git@${APPWORLD_REF}#subdirectory=experiments" \
  "vllm==${VLLM_VERSION}" "openai==${OPENAI_VERSION}" \
  "litellm==${LITELLM_VERSION}" "transformers==${TRANSFORMERS_VERSION}" \
  --extra-index-url https://download.pytorch.org/whl/cu128
python -m appworld.cli install
python -m pip check
python -m pip freeze > outputs/audits/requirements.lock.txt
python -c 'import appworld; print(appworld.__file__)'

