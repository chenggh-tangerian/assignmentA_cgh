#!/usr/bin/env bash
# =============================================================================
# 功能: 签名 SFT 全流程：备数据 → 训练 → 预测 → 评测 → 分析。
# 输入: GPU_ID 等环境变量
# 输出: sft/outputs_cgh/ 下模型、预测、评测与分析报告
# =============================================================================
# Full pipeline: prepare signature SFT data -> train -> predict -> eval -> analyze
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
LOG_FILE="${LOG_FILE:-${OUTPUTS_CGH}/sft_signature_full.log}"

cd "${PROJECT_ROOT}"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== [1/6] Prepare SFT train/valid/test with signatures =========="
"${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_mbpp_with_signature.py"
"${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_sft_train_with_signature.py"

echo "========== [2/6] Train SFT on signature-augmented data =========="
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/train_with_signature.sh"

echo "========== [3/6] Predict on MBPP (signature prompt) =========="
CONFIG="sft/scripts_cgh/configs/qwen15_predict_sft_with_signature.yaml" \
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/predict_with_signature.sh"

echo "========== [4/6] Execute evaluation =========="
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

echo "========== [5/6] Error analysis =========="
CASES="${EVAL_DIR}/mbpp_cases.jsonl" \
METRICS="${EVAL_DIR}/mbpp_metrics.json" \
OUTPUT_DIR="${ANALYSIS_DIR}" \
TAG="${TAG}" \
bash "${SCRIPT_DIR}/run_analysis.sh"

echo ""
echo "Done. Key outputs:"
echo "  model:       ${OUTPUTS_CGH}/qwen15_sft_with_signature"
echo "  metrics:     ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:      ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
echo "  log:         ${LOG_FILE}"
