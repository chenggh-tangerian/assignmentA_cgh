#!/usr/bin/env bash
# Predict/eval for ep6 model. Writes ONLY under sft_cgh_dataop/outputs_2/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
SFT_DIR="${PROJECT_ROOT}/sft"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_hq_sft_predict_ep6.yaml}"

PREDICT_DIR="${MODULE_DIR}/outputs_2/predict"
EVAL_DIR="${MODULE_DIR}/outputs_2/eval"
ANALYSIS_DIR="${MODULE_DIR}/outputs_2/analysis"
TAG="${TAG:-hq_sft_dataop_ep6}"
MODEL_DIR="${MODULE_DIR}/outputs_2/train/qwen15_hq_full_sft_ep6"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"
mkdir -p "${PREDICT_DIR}" "${EVAL_DIR}" "${ANALYSIS_DIR}"

if [[ ! -d "${MODEL_DIR}" ]]; then
  echo "Missing model: ${MODEL_DIR}"
  echo "Run: bash ${SCRIPT_DIR}/train_continue_ep6.sh"
  exit 1
fi

# Reuse signature MBPP already under module data/ (read-only; do not rewrite if present)
if [[ ! -f "${MODULE_DIR}/data/mbpp_sanitized_test_with_signature.json" ]]; then
  echo "Missing ${MODULE_DIR}/data/mbpp_sanitized_test_with_signature.json"
  exit 1
fi

echo "[predict_ep6] GPU=${GPU_ID} model=${MODEL_DIR}"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"

echo "[eval_ep6] MBPP execution"
"${PYTHON_BIN}" "${SFT_DIR}/scripts/evaluate_code_predictions.py" \
  --predictions "${PREDICT_DIR}/generated_predictions.jsonl" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --output_dir "${EVAL_DIR}" \
  --case_limit "${CASE_LIMIT:-257}" \
  --limit "${LIMIT:-0}" \
  --test_timeout "${TEST_TIMEOUT:-5.0}" \
  --memory_mb "${MEMORY_MB:-1024}"

echo "[analysis_ep6]"
"${PYTHON_BIN}" "${SFT_DIR}/scripts_cgh/analyze_errors.py" \
  --cases "${EVAL_DIR}/mbpp_cases.jsonl" \
  --metrics "${EVAL_DIR}/mbpp_metrics.json" \
  --output_dir "${ANALYSIS_DIR}" \
  --tag "${TAG}"

echo "[predict_ep6] done"
echo "  metrics: ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:  ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
