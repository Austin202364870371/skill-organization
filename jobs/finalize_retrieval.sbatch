#!/bin/bash
#SBATCH --job-name=skill-org-freeze-dev
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/finalize-retrieval-%j.out
#SBATCH --error=logs/finalize-retrieval-%j.err

set -euo pipefail
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
PYTHON_BIN="$PROJECT_DIR/env/bin/python"
FCSR_ROOT="${FCSR_ROOT:-/data-nfs/gpu3/u13256401368/fcsr}"
INFERENCE_DIR="${INFERENCE_DIR:-$PROJECT_DIR/data/fcsr_exchange/dev_inference_graph_v2}"
SNAPSHOTS="${SNAPSHOTS:-$PROJECT_DIR/data/fcsr_exchange/snapshots/dev_graph_v2.jsonl}"
PROVENANCE="${PROVENANCE:-$PROJECT_DIR/data/fcsr_exchange/dev_provenance_graph_v2.json}"
FREEZE_MANIFEST="${FREEZE_MANIFEST:-$PROJECT_DIR/freeze_manifest.graph-pd-v2.json}"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export TMPDIR="$PROJECT_DIR/.cache/tmp"
export PYTHONUNBUFFERED=1
mkdir -p logs "$TMPDIR" "$(dirname "$SNAPSHOTS")"
[[ -x "$PYTHON_BIN" ]] || { echo "Missing project Python" >&2; exit 1; }
[[ -f "$INFERENCE_DIR/rerank_records.jsonl" ]] || { echo "Missing rerank records" >&2; exit 1; }
[[ ! -e "$SNAPSHOTS" && ! -e "$PROVENANCE" && ! -e "$FREEZE_MANIFEST" ]] || {
  echo "Refusing to overwrite finalized v2 artifacts" >&2; exit 1;
}

log "Building and auditing 57 frozen Dev Top-5 snapshots"
"$PYTHON_BIN" scripts/finalize_dev_snapshots.py \
  --records "$INFERENCE_DIR/rerank_records.jsonl" \
  --queries data/fcsr_exchange/dev_queries.jsonl \
  --library-manifest skills/manifest.json \
  --fcsr-manifest "$FCSR_ROOT/checkpoints/fcsr/manifest.json" \
  --provenance-output "$PROVENANCE" \
  --snapshot-output "$SNAPSHOTS"

log "Freezing Library, evidence, organization, snapshots, model, prompt, and configs"
"$PYTHON_BIN" scripts/freeze_experiment.py \
  --snapshot "dev=$SNAPSHOTS" \
  --model-metadata models/model_metadata.json \
  --fcsr-manifest "$FCSR_ROOT/checkpoints/fcsr/manifest.json" \
  --output "$FREEZE_MANIFEST"
"$PYTHON_BIN" scripts/main.py verify-freeze --manifest "$FREEZE_MANIFEST"
"$PYTHON_BIN" scripts/verify_frozen_input.py --manifest "$FREEZE_MANIFEST" --path "$SNAPSHOTS"
log "Dev v2 freeze completed"
