#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
SFT_DIR="${PROJECT_ROOT}/sft"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_full_sft_predict.yaml}"
MODEL_DIR="${MODULE_DIR}/outputs/train/qwen15_dataop3_full_sft"
PREDICT_DIR="${MODULE_DIR}/outputs/predict"
EVAL_DIR="${MODULE_DIR}/outputs/eval"
ANALYSIS_DIR="${MODULE_DIR}/outputs/analysis"
TAG="${TAG:-dataop3}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"
mkdir -p "${PREDICT_DIR}" "${EVAL_DIR}" "${ANALYSIS_DIR}"
[[ -d "${MODEL_DIR}" ]] || { echo "Missing model ${MODEL_DIR}"; exit 1; }

echo "[predict] GPU=${GPU_ID}"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"

"${PYTHON_BIN}" "${SFT_DIR}/scripts/evaluate_code_predictions.py" \
  --predictions "${PREDICT_DIR}/generated_predictions.jsonl" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config sanitized --split test \
  --output_dir "${EVAL_DIR}" \
  --case_limit 257 --limit 0 --test_timeout 5.0 --memory_mb 1024

"${PYTHON_BIN}" "${SFT_DIR}/scripts_cgh/analyze_errors.py" \
  --cases "${EVAL_DIR}/mbpp_cases.jsonl" \
  --metrics "${EVAL_DIR}/mbpp_metrics.json" \
  --output_dir "${ANALYSIS_DIR}" \
  --tag "${TAG}"

echo "[predict] done -> ${EVAL_DIR}/mbpp_metrics.json"
