#!/usr/bin/env bash
# ToT 评测：thought → 剪枝 → code 扩展 → verifier 选优。
#
# 输入
#   - 环境变量（可选）:
#       MODEL_PATH          模型路径（默认 rl/outputs/train_lora_ppo_full/checkpoint-1304）
#       OUTPUT_DIR          输出目录（默认 a5_cgh/outputs/eval_tot）
#       MBPP_CONFIG / MBPP_SPLIT / PROMPT_MODE
#       BRANCH_FACTOR / BEAM_WIDTH / DEPTH（DEPTH 当前仅支持 2）
#       VALUE_MODE          heuristic|llm（默认 heuristic）
#       TEMPERATURE / TOP_P
#       MAX_NEW_TOKENS / MAX_THOUGHT_TOKENS / MAX_VALUE_TOKENS
#       BATCH_SIZE / GPU_ID
#       INPUT_PRICE_PER_1M / OUTPUT_PRICE_PER_1M
#   - 数据文件（经 mbpp_eval_tot.py）:
#       mbpp/{config}/{split}-00000-of-00001.parquet
#   - 模型目录: $MODEL_PATH
#
# 输出（默认 a5_cgh/outputs/eval_tot/）
#   - mbpp_tot_records.jsonl         每题完整搜索树
#   - mbpp_nodes_tot.jsonl           节点级落盘（与 records 同源）
#   - mbpp_cases_tot.jsonl           最终选中代码的判题结果
#   - mbpp_metrics_tot.json          pass@1_tot / oracle / token_cost / timing
#   - token_cost.json / timing.json
#   - mbpp_token_cost_per_task.jsonl
#
# Usage:
#   bash a5_cgh/scripts/eval_tot.sh
#   LIMIT=2 BRANCH_FACTOR=3 BEAM_WIDTH=2 bash a5_cgh/scripts/eval_tot.sh
#   VALUE_MODE=llm bash a5_cgh/scripts/eval_tot.sh
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
  echo "[eval_tot] GPU status before launch:"
  nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader || true
  echo "[eval_tot] Tip: do not run other evals or training on the same GPU concurrently."
fi

EXTRA_ARGS=()
if [[ -n "${LIMIT:-}" ]]; then
  EXTRA_ARGS+=(--limit "${LIMIT}")
fi
if [[ -n "${SKIP_GENERATION:-}" ]]; then
  EXTRA_ARGS+=(--skip_generation)
fi

"${PYTHON_BIN}" a5_cgh/mbpp_eval_tot.py \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --prompt_mode "${PROMPT_MODE:-zero_shot}" \
  --model_path "${MODEL_PATH:-rl/outputs/train_lora_ppo_full/checkpoint-1304}" \
  --output_dir "${OUTPUT_DIR:-a5_cgh/outputs/eval_tot}" \
  --batch_size "${BATCH_SIZE:-4}" \
  --max_new_tokens "${MAX_NEW_TOKENS:-512}" \
  --max_thought_tokens "${MAX_THOUGHT_TOKENS:-256}" \
  --max_value_tokens "${MAX_VALUE_TOKENS:-32}" \
  --branch_factor "${BRANCH_FACTOR:-3}" \
  --beam_width "${BEAM_WIDTH:-2}" \
  --depth "${DEPTH:-2}" \
  --temperature "${TEMPERATURE:-0.7}" \
  --top_p "${TOP_P:-0.95}" \
  --value_mode "${VALUE_MODE:-heuristic}" \
  --input_price_per_1m "${INPUT_PRICE_PER_1M:-0}" \
  --output_price_per_1m "${OUTPUT_PRICE_PER_1M:-0}" \
  "${EXTRA_ARGS[@]}" \
  "$@"
