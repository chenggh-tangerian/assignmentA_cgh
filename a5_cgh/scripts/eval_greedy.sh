#!/usr/bin/env bash
# Greedy 基线评测：MBPP 官方 [BEGIN]/[DONE] Prompt，temperature=0 单路径解码。
#
# 输入
#   - 环境变量（可选）:
#       MODEL_PATH          模型路径（默认 rl/outputs/train_lora_ppo_full/checkpoint-1304）
#       OUTPUT_DIR          输出目录（默认 a5_cgh/outputs/eval_greedy）
#       MBPP_CONFIG         sanitized|full（默认 sanitized）
#       MBPP_SPLIT          默认 test
#       PROMPT_MODE         zero_shot|one_shot|three_shot（默认 zero_shot）
#       LIMIT / BATCH_SIZE / MAX_NEW_TOKENS / GPU_ID
#       SKIP_GENERATION     非空则跳过推理，只重跑判题
#       INPUT_PRICE_PER_1M / OUTPUT_PRICE_PER_1M
#   - 数据文件（经 mbpp_eval_baseline.py）:
#       mbpp/{config}/{split}-00000-of-00001.parquet
#   - 模型目录: $MODEL_PATH
#
# 输出（默认 a5_cgh/outputs/eval_greedy/）
#   - mbpp_greedy_records.jsonl
#   - mbpp_cases_greedy.jsonl
#   - mbpp_metrics_greedy.json
#   - token_cost.json / timing.json
#   - mbpp_token_cost_per_task_greedy.jsonl
#
# Usage:
#   bash a5_cgh/scripts/eval_greedy.sh
#   LIMIT=20 MODEL_PATH=rl/outputs/train_lora_ppo_full/checkpoint-1304 bash a5_cgh/scripts/eval_greedy.sh
#   SKIP_GENERATION=1 bash a5_cgh/scripts/eval_greedy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
A5_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${A5_DIR}/.." && pwd)"

DEFAULT_PYTHON="/opt/conda/envs/cjqsft/bin/python"
if [[ -x "${DEFAULT_PYTHON}" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-${DEFAULT_PYTHON}}"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

GPU_ID="${GPU_ID:-0}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-0}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"

cd "${PROJECT_ROOT}"

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[eval_greedy] GPU status before launch:"
  nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader || true
  echo "[eval_greedy] Tip: do not run other evals or training on the same GPU concurrently."
fi

EXTRA_ARGS=()
if [[ -n "${LIMIT:-}" ]]; then
  EXTRA_ARGS+=(--limit "${LIMIT}")
fi
if [[ -n "${SKIP_GENERATION:-}" ]]; then
  EXTRA_ARGS+=(--skip_generation)
fi

"${PYTHON_BIN}" a5_cgh/mbpp_eval_baseline.py \
  --method greedy \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --prompt_mode "${PROMPT_MODE:-zero_shot}" \
  --model_path "${MODEL_PATH:-rl/outputs/train_lora_ppo_full/checkpoint-1304}" \
  --output_dir "${OUTPUT_DIR:-a5_cgh/outputs/eval_greedy}" \
  --batch_size "${BATCH_SIZE:-4}" \
  --max_new_tokens "${MAX_NEW_TOKENS:-512}" \
  --input_price_per_1m "${INPUT_PRICE_PER_1M:-0}" \
  --output_price_per_1m "${OUTPUT_PRICE_PER_1M:-0}" \
  "${EXTRA_ARGS[@]}" \
  "$@"
