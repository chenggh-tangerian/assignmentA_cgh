#!/usr/bin/env bash
# =============================================================================
# 功能: 调用 LLaMA-Factory 训练签名增强 Full SFT。
# 输入: CONFIG(默认 qwen15_sft_with_signature.yaml) / GPU_ID
# 输出: 配置中 output_dir（sft/outputs_cgh/qwen15_sft_with_signature）
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
CONFIG="${CONFIG:-sft/scripts_cgh/configs/qwen15_sft_with_signature.yaml}"
GPU_ID="${GPU_ID:-0}"
BASELINE_MODEL_DIR="${PROJECT_ROOT}/sft/outputs/qwen15_code_full_sft"

if grep -q "output_dir:.*qwen15_code_full_sft" "${PROJECT_ROOT}/${CONFIG}" 2>/dev/null; then
  echo "ERROR: config points to baseline output_dir. Refusing to train." >&2
  exit 1
fi
if [[ -d "${BASELINE_MODEL_DIR}" ]]; then
  echo "baseline preserved at: ${BASELINE_MODEL_DIR}"
fi
echo "new model will be saved under config output_dir (outputs_cgh/)"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" -c "import torch; print('project_root=', '${PROJECT_ROOT}'); print('CUDA_VISIBLE_DEVICES=', '${CUDA_VISIBLE_DEVICES}'); print('torch.cuda.is_available()=', torch.cuda.is_available()); print('visible_device_count=', torch.cuda.device_count()); print('device0=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
