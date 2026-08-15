#!/bin/bash
#SBATCH --job-name=skill-org-prepare
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=logs/prepare-%j.out
#SBATCH --error=logs/prepare-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
SPLIT="${SPLIT:?Set SPLIT to dev, test_normal, or test_challenge}"
cd "$PROJECT_DIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
export APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
mkdir -p logs data/fcsr_exchange

python scripts/validate_library.py --library skills/library
if [[ ! -f skills/manifest.json ]]; then
  python scripts/build_library_manifest.py --library skills/library --output skills/manifest.json
fi
python scripts/main.py export-skills --library skills/library \
  --output data/fcsr_exchange/skills_for_retrieval.jsonl
python scripts/export_appworld_tasks.py --split "$SPLIT" \
  --output "data/fcsr_exchange/${SPLIT}_queries.jsonl" \
  --inventory "data/fcsr_exchange/${SPLIT}_inventory.json"
