#!/usr/bin/env bash
# MBPP eval using the same protocol as dpo/scripts/eval.sh (mbpp_eval_dpo.py).
# All outputs under sft_cgh_dataop3/ only; invokes dpo script read-only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"

DEFAULT_PYTHON="/opt/conda/envs/cjqsft/bin/python"
if [[ -x "${DEFAULT_PYTHON}" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-${DEFAULT_PYTHON}}"
else
  PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
fi

GPU_ID="${GPU_ID:-0}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-0}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"

MODEL_PATH="${MODEL_PATH:-${MODULE_DIR}/outputs/train/qwen15_dataop3_full_sft}"
OUTPUT_DIR="${OUTPUT_DIR:-${MODULE_DIR}/outputs/eval_dpo}"
MBPP_DIR="${MBPP_DIR:-/root/siton-tmp/mbpp}"

mkdir -p "${OUTPUT_DIR}"

if [[ ! -d "${MODEL_PATH}" ]]; then
  echo "Missing model: ${MODEL_PATH}"
  exit 1
fi

cd "${PROJECT_ROOT}"

echo "[eval_dpo] model=${MODEL_PATH}"
echo "[eval_dpo] output=${OUTPUT_DIR}"
echo "[eval_dpo] protocol=dpo/scripts/mbpp_eval_dpo.py zero_shot"

"${PYTHON_BIN}" dpo/scripts/mbpp_eval_dpo.py \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --prompt_mode "${PROMPT_MODE:-zero_shot}" \
  --model_path "${MODEL_PATH}" \
  --output_dir "${OUTPUT_DIR}" \
  --mbpp_dir "${MBPP_DIR}" \
  --batch_size "${BATCH_SIZE:-8}" \
  --max_new_tokens "${MAX_NEW_TOKENS:-512}" \
  "$@"

echo "[eval_dpo] done -> ${OUTPUT_DIR}/mbpp_metrics.json"
