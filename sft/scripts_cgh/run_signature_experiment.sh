#!/usr/bin/env bash
# =============================================================================
# 功能: 仅推理侧实验——给 MBPP prompt 加签名，用已有 Full SFT 模型预测评测。
# 输入: MODEL_PATH(可选) / GPU_ID；不重新训练
# 输出: predict_with_signature / eval_with_signature 及错误分析
# =============================================================================
# Experiment: MBPP prompt with explicit function signature
# Pipeline: prepare data -> predict -> evaluate -> error analysis
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"

OUTPUTS_CGH="${PROJECT_ROOT}/sft/outputs_cgh"

PREDICT_DIR="${PREDICT_DIR:-${OUTPUTS_CGH}/predict_with_signature}"
EVAL_DIR="${EVAL_DIR:-${OUTPUTS_CGH}/eval_with_signature}"
ANALYSIS_DIR="${ANALYSIS_DIR:-${OUTPUTS_CGH}}"
TAG="${TAG:-with_signature}"
GPU_ID="${GPU_ID:-0}"
MODEL_PATH="${MODEL_PATH:-}"

cd "${PROJECT_ROOT}"

echo "========== [1/4] Prepare MBPP dataset with function signatures =========="
"${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_mbpp_with_signature.py"

echo "========== [2/4] Predict on signature-augmented MBPP =========="
GPU_ID="${GPU_ID}" MODEL_PATH="${MODEL_PATH}" bash "${SCRIPT_DIR}/predict_with_signature.sh"

echo "========== [3/4] Execute evaluation =========="
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

echo "========== [4/4] Error analysis =========="
CASES="${EVAL_DIR}/mbpp_cases.jsonl" \
METRICS="${EVAL_DIR}/mbpp_metrics.json" \
OUTPUT_DIR="${ANALYSIS_DIR}" \
TAG="${TAG}" \
bash "${SCRIPT_DIR}/run_analysis.sh"

echo ""
echo "Done. Key outputs:"
echo "  predictions: ${PREDICT_DIR}/generated_predictions.jsonl"
echo "  metrics:     ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:      ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
