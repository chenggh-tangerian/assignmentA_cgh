#!/usr/bin/env bash
# Train Full SFT on high-quality filtered data (sft_cgh_dataop only).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_hq_sft_train.yaml}"

# Same as sft/scripts/train.sh: llamafactory is source-loaded via PYTHONPATH, not pip-installed.
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"
mkdir -p "${MODULE_DIR}/outputs/train"

if [[ ! -f "${MODULE_DIR}/data/code_sft_train_hq.json" ]]; then
  echo "Missing filtered data. Run: bash ${SCRIPT_DIR}/run_filter.sh"
  exit 1
fi

if [[ ! -d "${LLAMA_FACTORY_DIR}/src/llamafactory" ]]; then
  echo "LlamaFactory not found at ${LLAMA_FACTORY_DIR}/src"
  echo "Set LLAMA_FACTORY_DIR to your local checkout."
  exit 1
fi

echo "[train] GPU=${GPU_ID} config=${CONFIG}"
echo "[train] PYTHONPATH+=${LLAMA_FACTORY_DIR}/src"
"${PYTHON_BIN}" -c "import torch; import llamafactory; print('torch.cuda.is_available()=', torch.cuda.is_available()); print('llamafactory ok')"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
echo "[train] done -> ${MODULE_DIR}/outputs/train/qwen15_hq_full_sft"
