#!/usr/bin/env bash
# Build high-quality filtered SFT datasets. Does not modify sft/data or other modules.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"

SOURCE_DIR="${SOURCE_DIR:-${PROJECT_ROOT}/sft/data}"
OUTPUT_DIR="${OUTPUT_DIR:-${MODULE_DIR}/data}"
REPORT_DIR="${REPORT_DIR:-${MODULE_DIR}/outputs/filter}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/filter_config.yaml}"
TARGET_TRAIN_SIZE="${TARGET_TRAIN_SIZE:-}"

cd "${PROJECT_ROOT}"
mkdir -p "${OUTPUT_DIR}" "${REPORT_DIR}"

EXTRA_ARGS=()
if [[ -n "${TARGET_TRAIN_SIZE}" ]]; then
  EXTRA_ARGS+=(--target_train_size "${TARGET_TRAIN_SIZE}")
fi

echo "[filter] source(read-only): ${SOURCE_DIR}"
echo "[filter] output:            ${OUTPUT_DIR}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/filter_high_quality.py" \
  --source_dir "${SOURCE_DIR}" \
  --output_dir "${OUTPUT_DIR}" \
  --report_dir "${REPORT_DIR}" \
  --config "${CONFIG}" \
  "${EXTRA_ARGS[@]}"

echo "[filter] done. See ${REPORT_DIR}/filter_report.md"
