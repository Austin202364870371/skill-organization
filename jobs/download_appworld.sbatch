#!/bin/bash
#SBATCH --job-name=skill-org-data
#SBATCH --qos=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=logs/download-%j.out
#SBATCH --error=logs/download-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
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
mkdir -p "$PIP_CACHE_DIR" "$HF_HOME" "$APPWORLD_CACHE" "$TORCH_HOME" "$TRITON_CACHE_DIR" \
  "$VLLM_CACHE_ROOT" "$VLLM_CONFIG_ROOT" "$CUDA_CACHE_PATH" "$NUMBA_CACHE_DIR" "$TMPDIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
mkdir -p logs "$APPWORLD_ROOT" outputs/audits
export APPWORLD_ROOT HF_HOME="$PROJECT_DIR/.cache/huggingface"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy

python -m appworld.cli install

download_with_resume() {
  local url="$1"
  local destination="$2"
  local attempt
  mkdir -p "$(dirname "$destination")"
  for attempt in $(seq 1 20); do
    echo "Download attempt $attempt: $url"
    if curl --fail --location --continue-at - --output "$destination" \
      --connect-timeout 30 --speed-time 120 --speed-limit 1024 "$url"; then
      return 0
    fi
    sleep 10
  done
  return 1
}

DATA_MARKER="$APPWORLD_ROOT/.data-0.2.0.complete"
DATA_BUNDLE="$APPWORLD_ROOT/.tmp/data.bundle"
if [[ ! -f "$DATA_MARKER" ]]; then
  if [[ -e "$APPWORLD_ROOT/data" ]]; then
    echo "Refusing to replace unmarked AppWorld data: $APPWORLD_ROOT/data" >&2
    exit 1
  fi
  export DATA_BUNDLE
  download_with_resume \
    "https://s3.us-west-2.amazonaws.com/appworld.dev/data-0.2.0.bundle" \
    "$DATA_BUNDLE"
  python - <<'PY'
import os
from appworld.common.constants import PASSWORD, SALT
from appworld.common.crypto import unpack_bundle

unpack_bundle(
    bundle_file_path=os.environ["DATA_BUNDLE"],
    base_directory=os.environ["APPWORLD_ROOT"],
    password=PASSWORD,
    salt=SALT,
)
PY
  rm -f "$DATA_BUNDLE"
  touch "$DATA_MARKER"
fi

OUTPUT_ROOT="$APPWORLD_ROOT/experiments/outputs"
OUTPUT_MARKER="$APPWORLD_ROOT/.experiment-outputs-0.1.3.complete"
OUTPUT_BUNDLE="$APPWORLD_ROOT/.tmp/experiment_outputs.bundle"
if [[ ! -f "$OUTPUT_MARKER" ]]; then
  export OUTPUT_ROOT OUTPUT_BUNDLE
  download_with_resume \
    "https://s3.us-west-2.amazonaws.com/appworld.dev/experiment-outputs-0.1.3.bundle" \
    "$OUTPUT_BUNDLE"
  mkdir -p "$OUTPUT_ROOT"
  python - <<'PY'
import os
from appworld.common.constants import PASSWORD, SALT
from appworld.common.crypto import unpack_bundle

unpack_bundle(
    bundle_file_path=os.environ["OUTPUT_BUNDLE"],
    base_directory=os.environ["OUTPUT_ROOT"],
    password=PASSWORD,
    salt=SALT,
)
PY
  rm -f "$OUTPUT_BUNDLE"
  touch "$OUTPUT_MARKER"
fi
python -m appworld.cli verify tests --root "$APPWORLD_ROOT"
python -m appworld.cli verify tasks --root "$APPWORLD_ROOT"
python scripts/main.py audit-appworld --root "$APPWORLD_ROOT" --output-dir outputs/audits
python scripts/audit_agent.py
OUTPUT_ROOT="$APPWORLD_ROOT/experiments/outputs"
if [[ -d "$OUTPUT_ROOT" ]]; then python scripts/main.py inspect-trajectories --root "$OUTPUT_ROOT" --output outputs/audits/trajectory_schema.json; fi

