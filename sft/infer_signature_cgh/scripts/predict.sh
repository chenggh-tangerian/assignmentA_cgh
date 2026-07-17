#!/usr/bin/env bash
# =============================================================================
# 功能: 已有 Full SFT 模型 + 签名增强 MBPP 做预测（推理侧优化，不改训练）。
# 输入: 本目录 configs 与环境变量 GPU_ID 等
# 输出: infer_signature_cgh/outputs/ 下预测结果
# =============================================================================
# Full SFT inference with signature-augmented MBPP prompts.
# Lives under sft/infer_signature_cgh/ — does not modify sft/scripts or sft/configs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SFT_DIR="$(cd "${MODULE_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
CONFIG="${CONFIG:-sft/infer_signature_cgh/configs/qwen15_full_sft_predict_with_signature.yaml}"
GPU_ID="${GPU_ID:-0}"
MODEL_PATH="${MODEL_PATH:-}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

cd "${PROJECT_ROOT}"

if [ -n "${MODEL_PATH}" ]; then
  echo "Using model path: ${MODEL_PATH}"
  TMP_CONFIG="$(mktemp "${MODULE_DIR}/outputs/.predict_config.XXXXXX.yaml")"
  "${PYTHON_BIN}" - "$CONFIG" "$MODEL_PATH" "$TMP_CONFIG" <<'PY'
import sys
from pathlib import Path
import yaml

config_path, model_path, out_path = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
data["model_name_or_path"] = model_path
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"Wrote override config to {out_path}")
PY
  CONFIG="$TMP_CONFIG"
fi

"${PYTHON_BIN}" -c "import torch; print('project_root=', '${PROJECT_ROOT}'); print('CUDA_VISIBLE_DEVICES=', '${CUDA_VISIBLE_DEVICES}'); print('torch.cuda.is_available()=', torch.cuda.is_available()); print('device0=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"
