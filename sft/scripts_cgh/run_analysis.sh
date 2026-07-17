#!/usr/bin/env bash
# =============================================================================
# 功能: 包装 analyze_errors.py，对评测 cases 做错误分类报告。
# 输入: CASES / METRICS / TAG；默认读 sft/outputs/eval_mbpp/
# 输出: OUTPUT_DIR（默认 sft/outputs_cgh）下的分析 md/json
# =============================================================================
# Error analysis wrapper — reads eval outputs, writes reports under sft/outputs_cgh/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CASES="${CASES:-${PROJECT_ROOT}/sft/outputs/eval_mbpp/mbpp_cases.jsonl}"
METRICS="${METRICS:-${PROJECT_ROOT}/sft/outputs/eval_mbpp/mbpp_metrics.json}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/sft/outputs_cgh}"
TAG="${TAG:-}"

echo "[error-analysis] cases=${CASES}"
echo "[error-analysis] metrics=${METRICS}"
echo "[error-analysis] output_dir=${OUTPUT_DIR}"

ARGS=(--cases "${CASES}" --output_dir "${OUTPUT_DIR}")
if [[ -f "${METRICS}" ]]; then
  ARGS+=(--metrics "${METRICS}")
fi
if [[ -n "${TAG}" ]]; then
  ARGS+=(--tag "${TAG}")
fi

/opt/conda/envs/chenggh-sft/bin/python "${SCRIPT_DIR}/analyze_errors.py" "${ARGS[@]}"
# TAG=with_signature CASES=${PROJECT_ROOT}/sft/outputs_cgh/predict_sft_with_signature/mbpp_cases.jsonl METRICS=${PROJECT_ROOT}/sft/outputs_cgh/predict_sft_with_signature/mbpp_metrics.json
