#!/usr/bin/env bash
# Continue HQ-SFT (+3 epochs) into outputs_2 only.
# Warm-starts from ep3 safetensors under outputs/ (read-only; no resume_from_checkpoint).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_hq_sft_train_continue_ep6.yaml}"
EP3_MODEL="${MODULE_DIR}/outputs/train/qwen15_hq_full_sft"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"
mkdir -p "${MODULE_DIR}/outputs_2/train"

if [[ ! -d "${EP3_MODEL}" ]]; then
  echo "Missing ep3 model: ${EP3_MODEL}"
  exit 1
fi
if [[ ! -f "${MODULE_DIR}/data/code_sft_train_hq.json" ]]; then
  echo "Missing filtered data. Run: bash ${SCRIPT_DIR}/run_filter.sh"
  exit 1
fi

echo "[train_ep6] GPU=${GPU_ID}"
echo "[train_ep6] warm-start(read-only): ${EP3_MODEL}"
echo "[train_ep6] output:                ${MODULE_DIR}/outputs_2/train/qwen15_hq_full_sft_ep6"
echo "[train_ep6] config:                ${CONFIG}"
"${PYTHON_BIN}" -c "import torch; import llamafactory; print('cuda=', torch.cuda.is_available(), 'llamafactory ok')"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
echo "[train_ep6] done -> ${MODULE_DIR}/outputs_2/train/qwen15_hq_full_sft_ep6"
