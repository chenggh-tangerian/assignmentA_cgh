#!/usr/bin/env bash
# 功能: 按 run_id 启动单次 LoRA 训练
# 输入: RUN_ID、对应 train yaml、GPU
# 输出: outputs/<run_id>/model/ 与训练日志
# 训练单组 LoRA/QLoRA（已完成则跳过）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

RUN_ID="${1:-}"
if [[ -z "${RUN_ID}" ]]; then
  echo "Usage: $0 <run_id>"
  echo "Example: $0 r8_tqv_q4"
  exit 1
fi

STATE_FILE="${STATE_DIR}/${RUN_ID}.json"
if [[ ! -f "${STATE_FILE}" ]]; then
  echo "State 文件不存在: ${STATE_FILE}，请先运行 00_init.sh"
  exit 1
fi

# sweep 里与已有配置完全相同的 alias：直接跳过
ALIAS_OF="$( "${PYTHON_BIN}" -c "import json; print(json.load(open('${STATE_FILE}')).get('alias_of') or '')" )"
if [[ -n "${ALIAS_OF}" ]]; then
  log_master "[01_train] SKIP ${RUN_ID} (alias of ${ALIAS_OF})"
  exit 0
fi

TRAIN_STATUS="$( "${PYTHON_BIN}" -c "import json; print(json.load(open('${STATE_FILE}'))['stages']['train']['status'])" )"
if [[ "${TRAIN_STATUS}" == "done" ]]; then
  log_master "[01_train] SKIP ${RUN_ID} (train already done)"
  exit 0
fi

TRAIN_CFG="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['train_config'])
" )"

MODEL_DIR_REL="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['model_dir'])
" )"

ensure_run_log_dir "${RUN_ID}"
TRAIN_LOG="$(run_log_dir "${RUN_ID}")/train.log"
GPU_CSV="$(run_log_dir "${RUN_ID}")/gpu_memory.csv"
RESOURCES_JSON="$(run_log_dir "${RUN_ID}")/resources_train.json"

cd_project_root
mkdir -p "${PROJECT_ROOT}/${MODEL_DIR_REL#./}"
MODEL_DIR="${PROJECT_ROOT}/${MODEL_DIR_REL#./}"

# 磁盘上已有完整产物：只补 resources / state
if [[ -f "${MODEL_DIR}/adapter_config.json" && -f "${MODEL_DIR}/train_results.json" ]]; then
  log_master "[01_train] SKIP ${RUN_ID} (artifacts on disk)"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/collect_train_stats.py" \
    --train-log "${TRAIN_LOG}" \
    --gpu-csv "${GPU_CSV}" \
    --model-dir "${MODEL_DIR}" \
    --output "${RESOURCES_JSON}" \
    --run-id "${RUN_ID}" \
    --manifest "${MANIFEST}" \
    --resume-checkpoint "" || true
  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" \
    --stage train \
    --status done \
    --set-resources "${RESOURCES_JSON}" || true
  "${PYTHON_BIN}" "${SCRIPT_DIR}/prune_checkpoints.py" --model-dir "${MODEL_DIR}" --keep 0 || true
  exit 0
fi

# 全新训练
: > "${TRAIN_LOG}"
echo "timestamp,index,memory_used_MiB,memory_total_MiB,memory_free_MiB,gpu_util_pct,temperature_c" > "${GPU_CSV}"

TRAIN_CFG_EFFECTIVE="${CONFIGS_DIR}/${RUN_ID}_train_effective.yaml"
"${PYTHON_BIN}" - <<PY
import yaml
from pathlib import Path
src = Path("${PROJECT_ROOT}") / "${TRAIN_CFG}"
out = Path("${TRAIN_CFG_EFFECTIVE}")
data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
data["overwrite_output_dir"] = True
data["resume_from_checkpoint"] = None
out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"Wrote {out}")
PY
TRAIN_CFG="sft/lora2_exp_cgh/configs/${RUN_ID}_train_effective.yaml"

log_master "[01_train] START ${RUN_ID} config=${TRAIN_CFG}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
  --state-file "${STATE_FILE}" \
  --stage train \
  --status running

MONITOR_PID=""
start_gpu_monitor "${RUN_ID}"
set +e
{
  echo "========== TRAIN ${RUN_ID} $(date '+%Y-%m-%d %H:%M:%S') =========="
  "${PYTHON_BIN}" -c "import torch; print('cuda=', torch.cuda.is_available()); print('device=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
  "${PYTHON_BIN}" -m llamafactory.cli train "${TRAIN_CFG}"
} 2>&1 | tee -a "${TRAIN_LOG}"
TRAIN_EXIT=${PIPESTATUS[0]}
set -e
stop_gpu_monitor "${MONITOR_PID}"

"${PYTHON_BIN}" "${SCRIPT_DIR}/collect_train_stats.py" \
  --train-log "${TRAIN_LOG}" \
  --gpu-csv "${GPU_CSV}" \
  --model-dir "${MODEL_DIR}" \
  --output "${RESOURCES_JSON}" \
  --run-id "${RUN_ID}" \
  --manifest "${MANIFEST}" \
  --resume-checkpoint "" || true

if [[ ${TRAIN_EXIT} -ne 0 ]] || [[ ! -f "${MODEL_DIR}/adapter_config.json" ]]; then
  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" \
    --stage train \
    --status failed \
    --error "train exit ${TRAIN_EXIT}, see ${TRAIN_LOG}"
  log_master "[01_train] FAILED ${RUN_ID}"
  exit "${TRAIN_EXIT:-1}"
fi

"${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
  --state-file "${STATE_FILE}" \
  --stage train \
  --status done \
  --set-resources "${RESOURCES_JSON}"

"${PYTHON_BIN}" "${SCRIPT_DIR}/prune_checkpoints.py" --model-dir "${MODEL_DIR}" --keep 0 || true
log_master "[01_train] DONE ${RUN_ID}"
