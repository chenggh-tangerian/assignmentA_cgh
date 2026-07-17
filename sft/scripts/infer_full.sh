#!/usr/bin/env bash
# =============================================================================
# 功能: 包装 infer.py，对微调模型做单条/批量交互式推理。
#
# 输入: 透传全部参数给 sft/scripts/infer.py（--model / --prompt / --prompts_file 等）
# 输出: infer.py 写出的 jsonl（默认 sft/outputs/infer_results.jsonl）
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SFT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" sft/scripts/infer.py "$@"
