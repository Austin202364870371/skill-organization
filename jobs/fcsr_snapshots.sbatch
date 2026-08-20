#!/bin/bash
#SBATCH --job-name=skill-org-fcsr
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --nodelist=GPU3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/fcsr-%j.out
#SBATCH --error=logs/fcsr-%j.err

set -euo pipefail
log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
FCSR_ROOT="${FCSR_ROOT:-/data-nfs/gpu3/u13256401368/fcsr}"
FCSR_CHECKPOINT="$FCSR_ROOT/checkpoints/fcsr"
PYTHON_BIN="$FCSR_ROOT/env-qgen/bin/python"
QUERIES="${QUERIES:-$PROJECT_DIR/data/fcsr_exchange/appworld_queries.jsonl}"
SKILLS="${SKILLS:-$PROJECT_DIR/data/fcsr_exchange/skills_for_retrieval.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/data/fcsr_exchange/inference}"
log "Job $SLURM_JOB_ID started on $(hostname)"
log "Project: $PROJECT_DIR"
log "FCSR root: $FCSR_ROOT"
log "Frozen checkpoint: $FCSR_CHECKPOINT"
cd "$FCSR_ROOT"
export XDG_CACHE_HOME="$FCSR_ROOT/.cache"
export PIP_CACHE_DIR="$FCSR_ROOT/.cache/pip"
export HF_HOME="$FCSR_ROOT/.cache/huggingface"
export TORCH_HOME="$FCSR_ROOT/.cache/torch"
export TRITON_CACHE_DIR="$FCSR_ROOT/.cache/triton"
export CUDA_CACHE_PATH="$FCSR_ROOT/.cache/cuda"
export NUMBA_CACHE_DIR="$FCSR_ROOT/.cache/numba"
export TMPDIR="$FCSR_ROOT/.cache/tmp"
export PYTHONUNBUFFERED=1
mkdir -p "$PIP_CACHE_DIR" "$HF_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" \
  "$CUDA_CACHE_PATH" "$NUMBA_CACHE_DIR" "$TMPDIR"
export HF_HOME="$FCSR_ROOT/.cache/huggingface" TOKENIZERS_PARALLELISM=false
[[ -x "$PYTHON_BIN" ]] || { echo "Missing FCSR Python: $PYTHON_BIN" >&2; exit 1; }
log "Using FCSR interpreter directly: $PYTHON_BIN"
"$PYTHON_BIN" -c 'import sys, torch, transformers, peft; print(f"python={sys.version.split()[0]} torch={torch.__version__} transformers={transformers.__version__} peft={peft.__version__}", flush=True)'

for path in "$QUERIES" "$SKILLS" "$FCSR_CHECKPOINT/manifest.json"; do
  [[ -f "$path" ]] || { echo "Missing input: $path" >&2; exit 1; }
done
for path in "$FCSR_CHECKPOINT/retriever" "$FCSR_CHECKPOINT/reranker"; do
  [[ -d "$path" ]] || { echo "Missing frozen checkpoint: $path" >&2; exit 1; }
done
[[ ! -e "$OUTPUT_DIR" ]] || { echo "Refusing to overwrite: $OUTPUT_DIR" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
log "Inputs verified: $(wc -l < "$QUERIES") queries, $(wc -l < "$SKILLS") skills"
log "Retriever base: $(grep -m1 'base_model_name_or_path' "$FCSR_CHECKPOINT/retriever/adapter_config.json")"
log "Reranker base: $(grep -m1 'base_model_name_or_path' "$FCSR_CHECKPOINT/reranker/adapter_config.json")"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
log "Starting hybrid retrieval (base model load begins now)"

"$PYTHON_BIN" -u -B scripts/evaluate.py hybrid \
  --queries "$QUERIES" --skills "$SKILLS" --model "$FCSR_CHECKPOINT/retriever" \
  --top-k 50 --fusion-depth 100 --rrf-k 60 --batch-size 8 \
  --query-max-length 512 --skill-max-length 2048 --device cuda \
  --output-predictions "$OUTPUT_DIR/retrieval_predictions.json" \
  --output-records "$OUTPUT_DIR/retrieval_records.jsonl"

log "Hybrid retrieval completed"
ls -lh "$OUTPUT_DIR/retrieval_predictions.json" "$OUTPUT_DIR/retrieval_records.jsonl"
log "Starting reranking (base model load begins now)"

"$PYTHON_BIN" -u -B scripts/evaluate.py rerank \
  --retrieval-records "$OUTPUT_DIR/retrieval_records.jsonl" --skills "$SKILLS" \
  --model "$FCSR_CHECKPOINT/reranker" --top-k 20 --batch-size 4 --max-length 4096 \
  --device cuda --output-predictions "$OUTPUT_DIR/rerank_predictions.json" \
  --output-records "$OUTPUT_DIR/rerank_records.jsonl"

log "Reranking completed"
ls -lh "$OUTPUT_DIR/rerank_predictions.json" "$OUTPUT_DIR/rerank_records.jsonl"
log "FCSR snapshot inference finished successfully"
