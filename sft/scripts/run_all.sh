#!/usr/bin/env bash
# =============================================================================
# 功能: 一键跑通主线 —— 准备数据 → Full SFT 训练 → MBPP 预测 → 执行评测。
#
# 输入: 无额外参数；各子脚本可用环境变量覆盖路径/配置。
# 输出:
#   sft/data/*                         训练数据
#   sft/outputs/qwen15_code_full_sft/  训练产物
#   sft/outputs/qwen15_code_full_predict/  预测
#   sft/outputs/eval_mbpp*/            评测指标
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

"${SFT_DIR}/scripts/prepare_data.sh"
"${SFT_DIR}/scripts/train.sh"
"${SFT_DIR}/scripts/predict_full.sh"
"${SFT_DIR}/scripts/evaluate_full.sh"
