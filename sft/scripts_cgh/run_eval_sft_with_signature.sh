#!/usr/bin/env bash
# =============================================================================
# 功能: 签名版 v2 模型：预测 → MBPP 执行评测 → 错误分析。
# 输入: GPU_ID；模型/配置见 predict 配置 yaml
# 输出: PREDICT_DIR / EVAL_DIR 下的 predictions、metrics、cases
# =============================================================================
# Predict + MBPP eval + error analysis for retrained v2 model only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
OUTPUTS_CGH="${PROJECT_ROOT}/sft/outputs_cgh"

GPU_ID="${GPU_ID:-0}"
TAG="${TAG:-sft_sig_retrain}"
PREDICT_DIR="${PREDICT_DIR:-${OUTPUTS_CGH}/predict_sft_with_signature}"
EVAL_DIR="${EVAL_DIR:-${OUTPUTS_CGH}/eval_sft_with_signature}"
ANALYSIS_DIR="${ANALYSIS_DIR:-${OUTPUTS_CGH}}"
LOG_FILE="${LOG_FILE:-${OUTPUTS_CGH}/eval_sft_with_signature.log}"

cd "${PROJECT_ROOT}"

exec > >(tee "${LOG_FILE}") 2>&1

echo "========== [1/3] Predict (v2 model + signature prompt) =========="
CONFIG="sft/scripts_cgh/configs/qwen15_predict_sft_with_signature.yaml" \
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/predict_with_signature.sh"

echo "========== [2/3] Execute MBPP evaluation =========="
"${PYTHON_BIN}" sft/scripts/evaluate_code_predictions.py \
  --predictions "${PREDICT_DIR}/generated_predictions.jsonl" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --output_dir "${EVAL_DIR}" \
  --case_limit "${CASE_LIMIT:-257}" \
  --limit "${LIMIT:-0}" \
  --test_timeout "${TEST_TIMEOUT:-5.0}" \
  --memory_mb "${MEMORY_MB:-1024}"

echo "========== [3/3] Error analysis =========="
CASES="${EVAL_DIR}/mbpp_cases.jsonl" \
METRICS="${EVAL_DIR}/mbpp_metrics.json" \
OUTPUT_DIR="${ANALYSIS_DIR}" \
TAG="${TAG}" \
bash "${SCRIPT_DIR}/run_analysis.sh"

echo ""
echo "Done."
echo "  metrics: ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:  ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
