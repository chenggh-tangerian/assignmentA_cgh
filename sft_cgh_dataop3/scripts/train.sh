#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_full_sft_train.yaml}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"
mkdir -p "${MODULE_DIR}/outputs/train"
[[ -f "${MODULE_DIR}/data/code_sft_train.json" ]] || { echo "Run build_data.sh first"; exit 1; }

echo "[train] GPU=${GPU_ID} -> ${MODULE_DIR}/outputs/train/qwen15_dataop3_full_sft"
"${PYTHON_BIN}" -c "import torch,llamafactory; print('cuda=', torch.cuda.is_available())"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
echo "[train] done"
