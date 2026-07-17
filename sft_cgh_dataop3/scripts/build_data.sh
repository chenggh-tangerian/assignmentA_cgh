#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
cd "${PROJECT_ROOT}"
mkdir -p "${MODULE_DIR}/data" "${MODULE_DIR}/outputs/filter"
"${PYTHON_BIN}" "${SCRIPT_DIR}/build_data.py" "$@"
echo "[build] done -> ${MODULE_DIR}/data (~60% of sft/data train, no test leak)"
