#!/bin/bash
#SBATCH --job-name=skill-org-evaluate
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=logs/evaluate-%j.out
#SBATCH --error=logs/evaluate-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
SPLIT="${SPLIT:?Set SPLIT to dev, test_normal, or test_challenge}"
APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
cd "$PROJECT_DIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
mkdir -p logs outputs/results/official

for SEED in 42 43 44; do
  for CONDITION in No-Skill Flat-NoPD Flat-PD Hierarchy-PD Graph-PD; do
    SAFE_CONDITION="${CONDITION//-/_}"
    SAFE_CONDITION="${SAFE_CONDITION,,}"
    EXPERIMENT="skill_organization__${SPLIT}__${SAFE_CONDITION}__seed_${SEED}"
    python -m appworld.cli evaluate "$EXPERIMENT" "$SPLIT" --root "$APPWORLD_ROOT"
  done
done

python scripts/collect_official_metrics.py \
  --appworld-root "$APPWORLD_ROOT" --split "$SPLIT" \
  --output "outputs/results/official/${SPLIT}.json"
python scripts/main.py analyze --runs outputs/runs --output outputs/results/summary.json
