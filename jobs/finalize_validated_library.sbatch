#!/bin/bash
#SBATCH --job-name=skill-org-finalize
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/finalize-library-%j.out
#SBATCH --error=logs/finalize-library-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export TMPDIR="$PROJECT_DIR/.cache/tmp"
mkdir -p "$TMPDIR" logs
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
python scripts/finalize_validated_library.py
