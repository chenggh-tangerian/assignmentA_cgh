#!/usr/bin/env bash
# =============================================================================
# 功能: 准备带函数签名的 SFT 训练数据 + MBPP 评测数据到 sft/data_cgh/。
# 输入: SOURCE_DIR(默认 sft/data)、SOURCE_MBPP；可选 DROP_NO_SIGNATURE=1
# 输出: OUTPUT_DIR 下 code_sft_*_with_signature.json、mbpp_*_with_signature.json
# =============================================================================
# Prepare signature-augmented SFT + MBPP eval data into sft/data_cgh/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"

SOURCE_DIR="${SOURCE_DIR:-${PROJECT_ROOT}/sft/data}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_ROOT}/sft/data_cgh}"
SOURCE_MBPP="${SOURCE_MBPP:-${SOURCE_DIR}/mbpp_sanitized_test.json}"
OUTPUT_MBPP="${OUTPUT_MBPP:-${OUTPUT_DIR}/mbpp_sanitized_test_with_signature.json}"
DROP_NO_SIGNATURE="${DROP_NO_SIGNATURE:-0}"
LOG_FILE="${LOG_FILE:-}"

cd "${PROJECT_ROOT}"

run() {
  if [[ -n "${LOG_FILE}" ]]; then
    "$@" | tee -a "${LOG_FILE}"
  else
    "$@"
  fi
}

echo "========== Prepare signature-augmented data =========="
echo "project_root:  ${PROJECT_ROOT}"
echo "source_dir:    ${SOURCE_DIR}"
echo "output_dir:    ${OUTPUT_DIR}"
echo "source_mbpp:   ${SOURCE_MBPP}"
echo "output_mbpp:   ${OUTPUT_MBPP}"

DROP_ARGS=()
if [[ "${DROP_NO_SIGNATURE}" == "1" ]]; then
  DROP_ARGS=(--drop-no-signature)
fi

run "${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_mbpp_with_signature.py" \
  --source "${SOURCE_MBPP}" \
  --output "${OUTPUT_MBPP}"

run "${PYTHON_BIN}" "${SCRIPT_DIR}/prepare_sft_train_with_signature.py" \
  --source_dir "${SOURCE_DIR}" \
  --output_dir "${OUTPUT_DIR}" \
  "${DROP_ARGS[@]}"

echo ""
echo "Done. Outputs:"
echo "  data dir:       ${OUTPUT_DIR}"
echo "  dataset_info:   ${OUTPUT_DIR}/dataset_info.json"
echo "  mbpp eval:      ${OUTPUT_MBPP}"
echo "  train/valid/test: ${OUTPUT_DIR}/code_sft_{train,valid,test}_with_signature.json"
