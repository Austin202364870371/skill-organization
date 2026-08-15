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
mkdir -p logs .cache/huggingface outputs/audits

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

