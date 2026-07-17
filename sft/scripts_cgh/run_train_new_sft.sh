#!/usr/bin/env bash
# =============================================================================
# 功能: 用签名增强数据训练新版 SFT（不覆盖 baseline 模型目录）。
# 输入: GPU_ID；数据由 prepare_*_with_signature 生成
# 输出: sft/outputs_cgh/qwen15_sft_with_signature/
# =============================================================================
# 训练新版 SFT（带函数签名的数据），超参与 baseline 一致。
# baseline 保留在 sft/outputs/qwen15_code_full_sft/，本脚本不会写入该目录。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"

BASELINE_MODEL_DIR="${PROJECT_ROOT}/sft/outputs/qwen15_code_full_sft"
NEW_MODEL_DIR="${PROJECT_ROOT}/sft/outputs_cgh/qwen15_sft_with_signature"
LOG_FILE="${LOG_FILE:-${PROJECT_ROOT}/sft/outputs_cgh/train_new_sft.log}"
GPU_ID="${GPU_ID:-0}"

if [[ "${NEW_MODEL_DIR}" == "${BASELINE_MODEL_DIR}" ]]; then
  echo "ERROR: new model dir must differ from baseline." >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

{
  echo "========== $(date -Iseconds) Train new SFT (v2 signature) =========="
  echo "baseline (read-only): ${BASELINE_MODEL_DIR}"
  echo "new model output:     ${NEW_MODEL_DIR}"
  echo "GPU_ID:               ${GPU_ID}"

  echo "========== [1/2] Prepare signature-augmented data =========="
  "${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_mbpp_with_signature.py"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_sft_train_with_signature.py"

  echo "========== [2/2] Train (same hyperparams as baseline) =========="
  GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/train_with_signature.sh"

  echo "========== Done: $(date -Iseconds) =========="
} 2>&1 | tee -a "${LOG_FILE}"
