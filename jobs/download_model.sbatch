#!/bin/bash
#SBATCH --job-name=skill-org-model
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=logs/model-%j.out
#SBATCH --error=logs/model-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
MODEL_REF="${MODEL_REF:-b2cff646eb4bb1d68355c01b18ae02e7cf42d120}"
MODEL_DIR="$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct"
cd "$PROJECT_DIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
[[ ! -e "$MODEL_DIR" ]] || { echo "Model directory already exists: $MODEL_DIR" >&2; exit 1; }
mkdir -p logs models .cache/huggingface
export HF_HOME="$PROJECT_DIR/.cache/huggingface" MODEL_REF MODEL_DIR
df -h "$PROJECT_DIR"
python - <<'PY'
import os
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="Qwen/Qwen3-Coder-30B-A3B-Instruct",
    revision=os.environ["MODEL_REF"],
    local_dir=os.environ["MODEL_DIR"],
)
PY
python scripts/record_model_metadata.py --model "$MODEL_DIR" --revision "$MODEL_REF" --output models/model_metadata.json
