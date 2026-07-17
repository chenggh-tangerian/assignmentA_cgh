#!/usr/bin/env bash
# 功能: 初始化 LoRA2 实验目录、manifest、数据与状态
# 输入: 无（或环境变量覆盖路径）
# 输出: manifest.json、data/、state/、configs/
# Stage 0: 生成 Phase1 manifest 与各 run 配置
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

FORCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE="--force"; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd_project_root
log_master "[00_init] 准备数据目录"
"${PYTHON_BIN}" "${SCRIPT_DIR}/setup_data.py" \
  --exp-dir "${EXP_DIR}" \
  --mbpp-dir "${MBPP_DIR}"

log_master "[00_init] 生成 manifest 与 Phase1 配置"

"${PYTHON_BIN}" "${SCRIPT_DIR}/generate_manifest.py" \
  --exp-dir "${EXP_DIR}" \
  --base-model "${BASE_MODEL}" \
  --dataset-dir "${DATASET_DIR}" \
  ${FORCE}

log_master "[00_init] 完成，Phase1 组数: $( "${PYTHON_BIN}" -c "import json; print(len(json.load(open('${MANIFEST}'))['runs']))" )"
