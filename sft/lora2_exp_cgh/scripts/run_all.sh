#!/usr/bin/env bash
# 功能: 一键跑完 LoRA2 网格：init→逐 run 训练/评测→报告
# 输入: GPU 等环境变量
# 输出: 全部 outputs/、state/、reports/
# 一键跑完：Phase1 网格 → alpha sweep → epoch sweep → 报告
#
# Usage:
#   GPU_ID=0 bash sft/lora2_exp_cgh/scripts/run_all.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

cd_project_root
log_master "[run_all] START GPU=${CUDA_VISIBLE_DEVICES}"

bash "${SCRIPT_DIR}/00_init.sh"

run_ids_for_phase() {
  local phase="$1"
  "${PYTHON_BIN}" - <<PY
import json
m = json.load(open("${MANIFEST}"))
ids = m.get("phases", {}).get("${phase}", {}).get("run_ids", [])
print(" ".join(ids))
PY
}

run_phase() {
  local name="$1"
  shift
  local ids=("$@")
  if [[ ${#ids[@]} -eq 0 ]]; then
    log_master "[run_all] ${name}: 无 run"
    return 0
  fi
  log_master "[run_all] ${name}: ${ids[*]}"
  for RUN_ID in "${ids[@]}"; do
    bash "${SCRIPT_DIR}/01_train_run.sh" "${RUN_ID}"
    bash "${SCRIPT_DIR}/02_predict_eval_run.sh" "${RUN_ID}"
  done
}

# Phase1
mapfile -t GRID_IDS < <(run_ids_for_phase grid | tr ' ' '\n' | sed '/^$/d')
run_phase "Phase1-grid" "${GRID_IDS[@]:-}"

# Phase2 alpha
log_master "[run_all] generate alpha sweep"
"${PYTHON_BIN}" "${SCRIPT_DIR}/generate_sweep_runs.py" --exp-dir "${EXP_DIR}" --phase alpha
mapfile -t ALPHA_IDS < <(run_ids_for_phase alpha_sweep | tr ' ' '\n' | sed '/^$/d')
run_phase "Phase2-alpha" "${ALPHA_IDS[@]:-}"

# Phase3 epoch
log_master "[run_all] generate epoch sweep"
"${PYTHON_BIN}" "${SCRIPT_DIR}/generate_sweep_runs.py" --exp-dir "${EXP_DIR}" --phase epoch
mapfile -t EPOCH_IDS < <(run_ids_for_phase epoch_sweep | tr ' ' '\n' | sed '/^$/d')
run_phase "Phase3-epoch" "${EPOCH_IDS[@]:-}"

bash "${SCRIPT_DIR}/03_report.sh"
log_master "[run_all] FINISHED"
echo ""
echo "报告: ${REPORTS_DIR}/experiment_report.md"
echo "可视化: ${REPORTS_DIR}/lora2_acceptance_dashboard.html"
