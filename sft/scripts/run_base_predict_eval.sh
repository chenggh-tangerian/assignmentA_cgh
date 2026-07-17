#!/usr/bin/env bash
# =============================================================================
# 功能: 基座模型（未 SFT）在 MBPP 上预测 + 执行评测，作对照基线。
#
# 输入:
#   BASE_MODEL   默认 ./Qwen1.5-0.5B-Chat
#   CONFIG       默认 sft/configs/qwen15_code_base_predict.yaml
#   PREDICT_DIR / EVAL_DIR
#
# 输出:
#   ${PREDICT_DIR}/generated_predictions.jsonl
#   ${EVAL_DIR}/mbpp_metrics.json / mbpp_cases.jsonl
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"

BASE_MODEL="${BASE_MODEL:-./Qwen1.5-0.5B-Chat}"
CONFIG="${CONFIG:-sft/configs/qwen15_code_base_predict.yaml}"
PREDICT_DIR="${PREDICT_DIR:-sft/outputs/qwen15_code_base_predict}"
EVAL_DIR="${EVAL_DIR:-sft/outputs/eval_mbpp_base}"

echo "==> [1/2] Predict with base model (no SFT): ${BASE_MODEL}"
MODEL_PATH="${BASE_MODEL}" \
  CONFIG="${CONFIG}" \
  "${SFT_DIR}/scripts/predict_full.sh"

echo "==> [2/2] Evaluate predictions"
PREDICTIONS="${PREDICT_DIR}/generated_predictions.jsonl" \
  EVAL_DIR="${EVAL_DIR}" \
  "${SFT_DIR}/scripts/evaluate_full.sh"

echo "Done."
echo "  predictions: ${PREDICT_DIR}/generated_predictions.jsonl"
echo "  metrics:     ${EVAL_DIR}/mbpp_metrics.json"
echo "  cases:       ${EVAL_DIR}/mbpp_cases.jsonl"
