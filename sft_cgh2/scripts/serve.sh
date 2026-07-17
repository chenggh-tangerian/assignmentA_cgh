#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON="${PYTHON_BIN:-/opt/conda/envs/cjqsft/bin/python}"
if [[ ! -x "${PYTHON}" ]]; then PYTHON=python3; fi

export GPU_ID="${GPU_ID:-0}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PORT="${PORT:-8081}"

cd "${PROJECT_ROOT}"
echo "Starting sft_cgh2 repair (frontend + /repair) on port ${PORT}"
exec "${PYTHON}" sft_cgh2/scripts/serve_repair.py
