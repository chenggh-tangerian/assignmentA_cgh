#!/usr/bin/env bash
# =============================================================================
# 功能: 公平对比评测——v2 模型 + 与 baseline 相同的无签名 MBPP prompt。
# 输入: GPU_ID；baseline 指标只读对照
# 输出: predict_v2_fair_compare / eval_v2_fair_compare
# =============================================================================
# Fair eval: same MBPP prompt & generation settings as baseline, only model is v2.
# baseline results: sft/outputs/eval_mbpp/mbpp_metrics.json  (pass@1 ~3.1%)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
OUTPUTS_CGH="${PROJECT_ROOT}/sft/outputs_cgh"

GPU_ID="${GPU_ID:-0}"
TAG="${TAG:-v2_fair_compare}"
PREDICT_DIR="${PREDICT_DIR:-${OUTPUTS_CGH}/predict_v2_fair_compare}"
EVAL_DIR="${EVAL_DIR:-${OUTPUTS_CGH}/eval_v2_fair_compare}"
ANALYSIS_DIR="${ANALYSIS_DIR:-${OUTPUTS_CGH}}"
LOG_FILE="${LOG_FILE:-${OUTPUTS_CGH}/fair_compare_eval.log}"

cd "${PROJECT_ROOT}"

exec > >(tee "${LOG_FILE}") 2>&1

echo "========== Fair comparison eval (v2 model, baseline-style prompt) =========="
echo "baseline metrics (read-only): sft/outputs/eval_mbpp/mbpp_metrics.json"
echo "v2 model:                   sft/outputs_cgh/qwen15_sft_with_signature"
echo "prompt:                     sft/data/mbpp_sanitized_test.json (NO signature)"
echo ""

echo "========== [1/4] Sync original MBPP test set into data_cgh =========="
SRC_MBPP="${PROJECT_ROOT}/sft/data/mbpp_sanitized_test.json"
DST_MBPP="${PROJECT_ROOT}/sft/data_cgh/mbpp_sanitized_test.json"
if [[ ! -f "${SRC_MBPP}" ]]; then
  echo "ERROR: missing ${SRC_MBPP}" >&2
  exit 1
fi
cp "${SRC_MBPP}" "${DST_MBPP}"

INFO="${PROJECT_ROOT}/sft/data_cgh/dataset_info.json"
"${PYTHON_BIN}" - "${INFO}" <<'PY'
import json, sys
from pathlib import Path

info_path = Path(sys.argv[1])
data = {}
if info_path.exists():
    data = json.loads(info_path.read_text(encoding="utf-8"))
data["mbpp_sanitized_test"] = {"file_name": "mbpp_sanitized_test.json"}
info_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Updated {info_path}")
PY

echo "========== [2/4] Predict =========="
CONFIG="sft/scripts_cgh/configs/qwen15_predict_v2_fair_compare.yaml" \
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/predict_with_signature.sh"

echo "========== [3/4] Execute evaluation =========="
"${PYTHON_BIN}" sft/scripts/evaluate_code_predictions.py \
  --predictions "${PREDICT_DIR}/generated_predictions.jsonl" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --output_dir "${EVAL_DIR}" \
  --case_limit "${CASE_LIMIT:-257}" \
  --limit "${LIMIT:-0}" \
  --test_timeout "${TEST_TIMEOUT:-5.0}" \
  --memory_mb "${MEMORY_MB:-1024}"

echo "========== [4/4] Error analysis =========="
CASES="${EVAL_DIR}/mbpp_cases.jsonl" \
METRICS="${EVAL_DIR}/mbpp_metrics.json" \
OUTPUT_DIR="${ANALYSIS_DIR}" \
TAG="${TAG}" \
bash "${SCRIPT_DIR}/run_analysis.sh"

echo ""
echo "Done."
echo "  v2 fair metrics: ${EVAL_DIR}/mbpp_metrics.json"
echo "  v2 fair report:  ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
