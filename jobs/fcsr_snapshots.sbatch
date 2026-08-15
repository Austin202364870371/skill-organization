#!/bin/bash
#SBATCH --job-name=skill-org-fcsr
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --exclude=GPU0,GPU1,GPU4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/fcsr-%j.out
#SBATCH --error=logs/fcsr-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
FCSR_ROOT="${FCSR_ROOT:-/data-nfs/gpu3/u13256401368/fcsr}"
QUERIES="${QUERIES:-$PROJECT_DIR/data/fcsr_exchange/appworld_queries.jsonl}"
SKILLS="${SKILLS:-$PROJECT_DIR/data/fcsr_exchange/skills_for_retrieval.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/data/fcsr_exchange/inference}"
cd "$FCSR_ROOT"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$FCSR_ROOT/env-qgen"
export HF_HOME="$FCSR_ROOT/.cache/huggingface" TOKENIZERS_PARALLELISM=false

for path in "$QUERIES" "$SKILLS"; do
  [[ -f "$path" ]] || { echo "Missing input: $path" >&2; exit 1; }
done
[[ ! -e "$OUTPUT_DIR" ]] || { echo "Refusing to overwrite: $OUTPUT_DIR" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"

python -u -B scripts/evaluate.py hybrid \
  --queries "$QUERIES" --skills "$SKILLS" --model checkpoints/fcsr/retriever \
  --top-k 50 --fusion-depth 100 --rrf-k 60 --batch-size 8 \
  --query-max-length 512 --skill-max-length 2048 --device cuda \
  --output-predictions "$OUTPUT_DIR/retrieval_predictions.json" \
  --output-records "$OUTPUT_DIR/retrieval_records.jsonl"

python -u -B scripts/evaluate.py rerank \
  --retrieval-records "$OUTPUT_DIR/retrieval_records.jsonl" --skills "$SKILLS" \
  --model checkpoints/fcsr/reranker --top-k 20 --batch-size 4 --max-length 4096 \
  --device cuda --output-predictions "$OUTPUT_DIR/rerank_predictions.json" \
  --output-records "$OUTPUT_DIR/rerank_records.jsonl"

