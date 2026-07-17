#!/usr/bin/env bash
# 空闲 GPU 时自动启动一次代码修复 SFT 训练。
#
# 输入:
#   环境变量（均可选）:
#     GPU_ID                  监听的 GPU 编号，默认 0
#     CHECK_INTERVAL_SECONDS  忙时重检间隔秒数，默认 1800
#     PYTHON_BIN              Python 解释器，默认 chenggh-sft 环境
#     TRAIN_CONFIG            LLaMA-Factory 训练 yaml
#     RUN_NAME / LOG_DIR / STATE_DIR / LOG_FILE
#   以及 TRAIN_CONFIG 指向的训练配置与数据集
#
# 输出:
#   sft_cgh2/logs/auto_train_<RUN_NAME>.log   监控与训练日志
#   训练产物目录由 TRAIN_CONFIG 的 output_dir 决定
#   （默认 sft_cgh2/outputs/qwen15_repair_lora）
#
# 行为: 轮询 nvidia-smi，目标 GPU 无 compute 进程则启动训练一次后退出。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

GPU_ID="${GPU_ID:-0}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-1800}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
TRAIN_CONFIG="${TRAIN_CONFIG:-sft_cgh2/configs/qwen15_repair_lora_train.yaml}"
RUN_NAME="${RUN_NAME:-qwen15_repair_lora}"
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/sft_cgh2/logs}"
STATE_DIR="${STATE_DIR:-${PROJECT_ROOT}/sft_cgh2/state}"
LOCK_DIR="${STATE_DIR}/auto_train_${RUN_NAME}.lock"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/auto_train_${RUN_NAME}.log}"

mkdir -p "${LOG_DIR}" "${STATE_DIR}"

# 带时间戳写日志，同时打到终端和日志文件
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

if ! command -v nvidia-smi >/dev/null 2>&1; then
  log "ERROR: nvidia-smi not found. Cannot detect GPU usage."
  exit 1
fi

# 用目录锁防止多个 watcher 同时跑
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  log "Another auto-train watcher is already active: ${LOCK_DIR}"
  exit 1
fi
trap 'rmdir "${LOCK_DIR}" 2>/dev/null || true' EXIT

cd "${PROJECT_ROOT}"

if [[ ! -f "${TRAIN_CONFIG}" ]]; then
  log "ERROR: train config not found: ${TRAIN_CONFIG}"
  exit 1
fi

log "Watcher started."
log "GPU_ID=${GPU_ID}"
log "CHECK_INTERVAL_SECONDS=${CHECK_INTERVAL_SECONDS}"
log "TRAIN_CONFIG=${TRAIN_CONFIG}"
log "PYTHON_BIN=${PYTHON_BIN}"

while true; do
  # 查询目标 GPU 上正在跑的 compute 进程 PID
  mapfile -t GPU_PIDS < <(
    nvidia-smi \
      --id="${GPU_ID}" \
      --query-compute-apps=pid \
      --format=csv,noheader,nounits 2>/dev/null \
      | awk 'NF {print $1}'
  )

  if [[ "${#GPU_PIDS[@]}" -eq 0 ]]; then
    log "GPU ${GPU_ID} is free. Starting training once."
    export CUDA_VISIBLE_DEVICES="${GPU_ID}"
    {
      echo "========== TRAIN ${RUN_NAME} $(date '+%Y-%m-%d %H:%M:%S') =========="
      echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
      echo "config=${TRAIN_CONFIG}"
      "${PYTHON_BIN}" -c "import torch; print('cuda=', torch.cuda.is_available()); print('device=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
      "${PYTHON_BIN}" -m llamafactory.cli train "${TRAIN_CONFIG}"
    } 2>&1 | tee -a "${LOG_FILE}"
    TRAIN_EXIT="${PIPESTATUS[0]}"
    log "Training finished with exit code ${TRAIN_EXIT}."
    exit "${TRAIN_EXIT}"
  fi

  log "GPU ${GPU_ID} busy with PIDs: ${GPU_PIDS[*]}. Rechecking in ${CHECK_INTERVAL_SECONDS}s."
  sleep "${CHECK_INTERVAL_SECONDS}"
done
