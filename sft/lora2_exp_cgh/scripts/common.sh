#!/usr/bin/env bash
# 功能: LoRA2 实验公共环境变量与工具函数（被其他脚本 source）
# 输入: 无
# 输出: 导出 EXP_DIR/PYTHON_BIN 等变量与辅助函数
# LoRA2 实验共享环境（精简版）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SFT_DIR="$(cd "${EXP_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"

LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

GPU_ID="${GPU_ID:-0}"
GPU_MONITOR_INTERVAL="${GPU_MONITOR_INTERVAL:-5}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

MANIFEST="${EXP_DIR}/manifest.json"
STATE_DIR="${EXP_DIR}/state/runs"
LOGS_DIR="${EXP_DIR}/logs"
OUTPUTS_DIR="${EXP_DIR}/outputs"
CONFIGS_DIR="${EXP_DIR}/configs"
REPORTS_DIR="${EXP_DIR}/reports"
MASTER_LOG="${LOGS_DIR}/master.log"

BASE_MODEL="${BASE_MODEL:-./Qwen1.5-0.5B-Chat}"
DATASET_DIR="${DATASET_DIR:-./sft/lora2_exp_cgh/data}"
MBPP_DIR="${MBPP_DIR:-/root/siton-tmp/mbpp}"

log_master() {
  local msg="$1"
  mkdir -p "${LOGS_DIR}"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${msg}" | tee -a "${MASTER_LOG}"
}

run_dir() {
  echo "${OUTPUTS_DIR}/$1"
}

run_log_dir() {
  echo "${LOGS_DIR}/$1"
}

ensure_run_log_dir() {
  mkdir -p "$(run_log_dir "$1")"
}

start_gpu_monitor() {
  local run_id="$1"
  local out_csv
  out_csv="$(run_log_dir "${run_id}")/gpu_memory.csv"
  ensure_run_log_dir "${run_id}"
  bash "${SCRIPT_DIR}/monitor_gpu.sh" "${out_csv}" "${GPU_MONITOR_INTERVAL}" &
  MONITOR_PID=$!
}

stop_gpu_monitor() {
  local pid="$1"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" 2>/dev/null || true
    wait "${pid}" 2>/dev/null || true
  fi
}

cd_project_root() {
  cd "${PROJECT_ROOT}"
}
