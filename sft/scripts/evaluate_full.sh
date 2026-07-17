#!/usr/bin/env bash
# =============================================================================
# 功能: 对模型预测做 MBPP 执行评测（pass@1 / 语法率 / 测试通过率等）。
#
# 输入 (环境变量):
#   PREDICTIONS   预测 jsonl (默认 sft/outputs/qwen15_code_full_predict/generated_predictions.jsonl)
#   MBPP_DIR / MBPP_CONFIG / MBPP_SPLIT
#   EVAL_DIR / LIMIT / TEST_TIMEOUT / MEMORY_MB
#
# 输出:
#   ${EVAL_DIR}/mbpp_metrics.json
#   ${EVAL_DIR}/mbpp_cases.jsonl
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}" # chenggh的sft环境

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" sft/scripts/evaluate_code_predictions.py \
  --predictions "${PREDICTIONS:-sft/outputs/qwen15_code_full_predict/generated_predictions.jsonl}" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --output_dir "${EVAL_DIR:-sft/outputs/eval_mbpp2}" \
  --limit "${LIMIT:-0}" \
  --test_timeout "${TEST_TIMEOUT:-5.0}" \
  --memory_mb "${MEMORY_MB:-1024}"
