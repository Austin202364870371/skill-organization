#!/bin/bash
#SBATCH --job-name=skill-org-rebuild
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/rebuild-organization-%j.out
#SBATCH --error=logs/rebuild-organization-%j.err

set -euo pipefail
log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

PROJECT_DIR="${PROJECT_DIR:-$PWD}"
PYTHON_BIN="$PROJECT_DIR/env/bin/python"
cd "$PROJECT_DIR"
export XDG_CACHE_HOME="$PROJECT_DIR/.cache"
export PIP_CACHE_DIR="$PROJECT_DIR/.cache/pip"
export TMPDIR="$PROJECT_DIR/.cache/tmp"
export PYTHONUNBUFFERED=1
mkdir -p logs "$PIP_CACHE_DIR" "$TMPDIR" data/fcsr_exchange organization
[[ -x "$PYTHON_BIN" ]] || { echo "Missing project Python: $PYTHON_BIN" >&2; exit 1; }

log "Validating fixed Skill Library"
"$PYTHON_BIN" scripts/main.py validate-library --library skills/library

log "Rebuilding Skill manifest"
"$PYTHON_BIN" scripts/build_library_manifest.py \
  --library skills/library --output skills/manifest.json --overwrite
"$PYTHON_BIN" scripts/verify_library.py \
  --library skills/library --manifest skills/manifest.json

log "Extracting Train-only graph evidence"
"$PYTHON_BIN" scripts/main.py extract-graph-evidence \
  --library skills/library \
  --appworld-root data/appworld \
  --output organization/train_graph_evidence.json

log "Rebuilding global graph and hierarchy"
"$PYTHON_BIN" scripts/main.py build-graph \
  --library skills/library \
  --evidence organization/train_graph_evidence.json \
  --output organization/global_graph.json
"$PYTHON_BIN" scripts/main.py build-hierarchy \
  --library skills/library \
  --output organization/global_hierarchy.json

log "Re-exporting the 45 Skill retrieval corpus"
"$PYTHON_BIN" scripts/main.py export-skills \
  --library skills/library \
  --output data/fcsr_exchange/skills_for_retrieval.jsonl

log "Checking artifact counts"
"$PYTHON_BIN" -c 'import json; from pathlib import Path; e=json.loads(Path("organization/train_graph_evidence.json").read_text()); g=json.loads(Path("organization/global_graph.json").read_text()); print({"tasks": len(e["task_records"]), "formal_edges": e["formal_edge_counts"], "graph_nodes": len(g["nodes"]), "graph_edges": len(g["edges"]), "retrieval_skills": sum(1 for _ in Path("data/fcsr_exchange/skills_for_retrieval.jsonl").open())}, flush=True)'
log "Organization rebuild completed"
