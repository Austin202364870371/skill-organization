#!/bin/bash
#SBATCH --job-name=skill-org-validate
#SBATCH --qos=fast
#SBATCH --nodes=1
#SBATCH --nodelist=GPU4
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --output=logs/validate-%j.out
#SBATCH --error=logs/validate-%j.err

set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-$PWD}"
SKILL="${SKILL:?Set SKILL to one generated skill directory}"
MODEL_PATH="${MODEL_PATH:-$PROJECT_DIR/models/Qwen3-Coder-30B-A3B-Instruct}"
MODEL_PORT="${MODEL_PORT:-8000}"
cd "$PROJECT_DIR"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$PROJECT_DIR/env"
mkdir -p logs outputs/skill_generation/validation
export APPWORLD_ROOT="${APPWORLD_ROOT:-$PROJECT_DIR/data/appworld}"
export MODEL_BASE_URL="http://127.0.0.1:$MODEL_PORT/v1" MODEL_API_KEY=local
export MODEL_ID=Qwen/Qwen3-Coder-30B-A3B-Instruct MODEL_PORT

vllm serve "$MODEL_PATH" --host 127.0.0.1 --port "$MODEL_PORT" \
  --served-model-name "$MODEL_ID" --dtype bfloat16 --max-model-len 32768 \
  --gpu-memory-utilization 0.90 > "logs/vllm-$SLURM_JOB_ID.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT
python - <<'PY'
import os, time, urllib.request
for _ in range(180):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{os.environ['MODEL_PORT']}/health", timeout=2)
        break
    except Exception:
        time.sleep(5)
else:
    raise SystemExit("local vLLM server did not become healthy")
PY
python scripts/validate_skill.py --skill "$SKILL" --max-rounds 3 --seed 42
