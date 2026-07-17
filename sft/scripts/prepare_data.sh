#!/usr/bin/env bash
# =============================================================================
# 功能: 准备代码 SFT 训练集（Alpaca parquet → JSON）。
#
# 输入 (环境变量可覆盖):
#   SOURCE_DIR   默认 python_code_instructions_18k_alpaca
#   OUTPUT_DIR   默认 sft/data
#   LIMIT / TRAIN_RATIO / VALID_RATIO / SEED
#
# 输出:
#   code_sft_train.json / code_sft_valid.json / code_sft_test.json
#   dataset_info.json
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" sft/scripts/prepare_code_sft_data.py \
  --source_dir "${SOURCE_DIR:-python_code_instructions_18k_alpaca}" \
  --output_dir "${OUTPUT_DIR:-sft/data}" \
  --limit "${LIMIT:-0}" \
  --train_ratio "${TRAIN_RATIO:-0.90}" \
  --valid_ratio "${VALID_RATIO:-0.05}" \
  --seed "${SEED:-42}"
