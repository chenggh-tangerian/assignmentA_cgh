#!/usr/bin/env bash
# Full pipeline: filter -> (optional) train -> predict/eval/analysis
# All artifacts stay under sft_cgh_dataop/. Existing modules are not modified.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_FILE="${LOG_FILE:-${MODULE_DIR}/outputs/run.log}"
SKIP_TRAIN="${SKIP_TRAIN:-0}"
GPU_ID="${GPU_ID:-0}"

mkdir -p "${MODULE_DIR}/outputs"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== [1/3] High-quality data filter =========="
bash "${SCRIPT_DIR}/run_filter.sh"

if [[ "${SKIP_TRAIN}" != "1" ]]; then
  echo "========== [2/3] Train HQ Full SFT =========="
  GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/train.sh"
else
  echo "========== [2/3] Skip train (SKIP_TRAIN=1) =========="
fi

echo "========== [3/3] Predict + eval + analysis =========="
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/predict.sh"

echo ""
echo "Pipeline finished."
echo "  filter report: ${MODULE_DIR}/outputs/filter/filter_report.md"
echo "  model:         ${MODULE_DIR}/outputs/train/qwen15_hq_full_sft"
echo "  metrics:       ${MODULE_DIR}/outputs/eval/mbpp_metrics.json"
echo "  log:           ${LOG_FILE}"
