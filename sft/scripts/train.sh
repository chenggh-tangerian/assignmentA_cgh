#!/usr/bin/env bash
# =============================================================================
# 功能: 调用 LLaMA-Factory 对 Qwen1.5-0.5B-Chat 做代码 Full SFT 训练。
#
# 输入:
#   CONFIG              训练 yaml (默认 sft/configs/qwen15_code_full_sft.yaml)
#   GPU_ID / CUDA_VISIBLE_DEVICES
#   PYTHON_BIN / LLAMA_FACTORY_DIR
#   依赖数据: sft/data/code_sft_train.json 等 (见 prepare_data.sh)
#
# 输出:
#   模型与日志目录由 CONFIG 中 output_dir 决定
#   (默认 sft/outputs/qwen15_code_full_sft)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-/root/siton-tmp/assignment_A/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG="${CONFIG:-sft/configs/qwen15_code_full_sft.yaml}"
GPU_ID="${GPU_ID:-0}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" -c "import torch; print('project_root=', '${PROJECT_ROOT}'); print('CUDA_VISIBLE_DEVICES=', '${CUDA_VISIBLE_DEVICES}'); print('torch.cuda.is_available()=', torch.cuda.is_available()); print('visible_device_count=', torch.cuda.device_count()); print('device0=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
