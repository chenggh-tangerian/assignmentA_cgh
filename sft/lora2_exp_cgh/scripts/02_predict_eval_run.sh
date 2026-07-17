#!/usr/bin/env bash
# 功能: 对指定 run 做 MBPP 预测并执行评测
# 输入: RUN_ID、predict yaml、模型目录
# 输出: 预测 jsonl、eval metrics/cases、更新 state
# 单组：预测 + MBPP 执行评测（已完成则跳过）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

RUN_ID="${1:-}"
if [[ -z "${RUN_ID}" ]]; then
  echo "Usage: $0 <run_id>"
  exit 1
fi

STATE_FILE="${STATE_DIR}/${RUN_ID}.json"
if [[ ! -f "${STATE_FILE}" ]]; then
  echo "State 文件不存在: ${STATE_FILE}"
  exit 1
fi

ALIAS_OF="$( "${PYTHON_BIN}" -c "import json; print(json.load(open('${STATE_FILE}')).get('alias_of') or '')" )"
if [[ -n "${ALIAS_OF}" ]]; then
  log_master "[02_predict_eval] SKIP ${RUN_ID} (alias of ${ALIAS_OF})"
  exit 0
fi

read -r TRAIN_STATUS PREDICT_STATUS EVAL_STATUS <<< "$( "${PYTHON_BIN}" -c "
import json
s = json.load(open('${STATE_FILE}'))
print(s['stages']['train']['status'], s['stages']['predict']['status'], s['stages']['eval']['status'])
" )"

if [[ "${TRAIN_STATUS}" != "done" ]]; then
  echo "Train not done for ${RUN_ID} (status=${TRAIN_STATUS})"
  exit 1
fi

if [[ "${PREDICT_STATUS}" == "done" && "${EVAL_STATUS}" == "done" ]]; then
  log_master "[02_predict_eval] SKIP ${RUN_ID} (already done)"
  exit 0
fi

PREDICT_CFG="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['predict_config'])
" )"
PREDICT_DIR_REL="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['predict_dir'])
" )"
EVAL_DIR_REL="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['eval_dir'])
" )"
MODEL_DIR_REL="$( "${PYTHON_BIN}" -c "
import json
m = json.load(open('${MANIFEST}'))
all_runs = m.get('runs', []) + m.get('sweep_runs', [])
run = next(r for r in all_runs if r['run_id'] == '${RUN_ID}')
print(run['paths']['model_dir'])
" )"

ensure_run_log_dir "${RUN_ID}"
PREDICT_LOG="$(run_log_dir "${RUN_ID}")/predict.log"
EVAL_LOG="$(run_log_dir "${RUN_ID}")/eval.log"

cd_project_root
PREDICT_DIR="${PROJECT_ROOT}/${PREDICT_DIR_REL#./}"
EVAL_DIR="${PROJECT_ROOT}/${EVAL_DIR_REL#./}"
MODEL_DIR="${PROJECT_ROOT}/${MODEL_DIR_REL#./}"
mkdir -p "${PREDICT_DIR}" "${EVAL_DIR}"

ADAPTER_PATH="${MODEL_DIR}"
if [[ ! -f "${MODEL_DIR}/adapter_config.json" ]]; then
  echo "Missing adapter at ${MODEL_DIR}"
  exit 1
fi

PREDICT_CFG_EFFECTIVE="${CONFIGS_DIR}/${RUN_ID}_predict_effective.yaml"
"${PYTHON_BIN}" - <<PY
import yaml
from pathlib import Path
src = Path("${PROJECT_ROOT}") / "${PREDICT_CFG}"
out = Path("${PREDICT_CFG_EFFECTIVE}")
data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
data["adapter_name_or_path"] = "${ADAPTER_PATH}".replace("${PROJECT_ROOT}/", "./").replace("${PROJECT_ROOT}", ".")
out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"Wrote {out}")
PY

if [[ "${PREDICT_STATUS}" != "done" ]]; then
  log_master "[02_predict_eval] PREDICT START ${RUN_ID}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" --stage predict --status running

  MONITOR_PID=""
  start_gpu_monitor "${RUN_ID}"
  set +e
  {
    echo "========== PREDICT ${RUN_ID} $(date '+%Y-%m-%d %H:%M:%S') =========="
    "${PYTHON_BIN}" -m llamafactory.cli train "sft/lora2_exp_cgh/configs/${RUN_ID}_predict_effective.yaml"
  } 2>&1 | tee -a "${PREDICT_LOG}"
  PREDICT_EXIT=${PIPESTATUS[0]}
  set -e
  stop_gpu_monitor "${MONITOR_PID}"

  if [[ ${PREDICT_EXIT} -ne 0 ]]; then
    "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
      --state-file "${STATE_FILE}" --stage predict --status failed \
      --error "predict exit ${PREDICT_EXIT}"
    exit "${PREDICT_EXIT}"
  fi
  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" --stage predict --status done
fi

if [[ "${EVAL_STATUS}" != "done" ]]; then
  PREDICTIONS="${PREDICT_DIR}/generated_predictions.jsonl"
  if [[ ! -f "${PREDICTIONS}" ]]; then
    echo "Missing predictions: ${PREDICTIONS}"
    exit 1
  fi

  log_master "[02_predict_eval] EVAL START ${RUN_ID}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" --stage eval --status running

  set +e
  {
    echo "========== EVAL ${RUN_ID} $(date '+%Y-%m-%d %H:%M:%S') =========="
    "${PYTHON_BIN}" sft/scripts/evaluate_code_predictions.py \
      --predictions "${PREDICTIONS}" \
      --mbpp_dir "${MBPP_DIR}" \
      --config sanitized \
      --split test \
      --output_dir "${EVAL_DIR}" \
      --case_limit "${EVAL_CASE_LIMIT:-257}" \
      --limit 0 \
      --test_timeout 5.0 \
      --memory_mb 1024
  } 2>&1 | tee -a "${EVAL_LOG}"
  EVAL_EXIT=${PIPESTATUS[0]}
  set -e

  if [[ ${EVAL_EXIT} -ne 0 ]]; then
    "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
      --state-file "${STATE_FILE}" --stage eval --status failed \
      --error "eval exit ${EVAL_EXIT}"
    exit "${EVAL_EXIT}"
  fi

  "${PYTHON_BIN}" "${SCRIPT_DIR}/update_state.py" \
    --state-file "${STATE_FILE}" \
    --stage eval \
    --status done \
    --set-metrics "${EVAL_DIR}/mbpp_metrics.json"
  log_master "[02_predict_eval] DONE ${RUN_ID}"
fi
