#!/usr/bin/env bash
# =============================================================================
# 功能: 推理侧签名优化一键流程（备数据→预测→评测→分析），不重训。
# 输入: 已有 Full SFT 权重；产物全部落在 infer_signature_cgh/
# 输出: 本目录 outputs/ 下预测、评测、分析
# =============================================================================
# Inference-only signature optimization for Full SFT.
# All new artifacts stay under sft/infer_signature_cgh/.
# Does NOT retrain. Does NOT modify sft/scripts, sft/configs, or sft/data.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SFT_DIR="$(cd "${MODULE_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${SFT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"

DATA_DIR="${MODULE_DIR}/data"
PREDICT_DIR="${MODULE_DIR}/outputs/predict"
EVAL_DIR="${MODULE_DIR}/outputs/eval"
ANALYSIS_DIR="${MODULE_DIR}/outputs/analysis"
TAG="${TAG:-full_sft_infer_signature}"
LOG_FILE="${LOG_FILE:-${MODULE_DIR}/outputs/run.log}"

MBPP_SOURCE="${MBPP_SOURCE:-${SFT_DIR}/data/mbpp_sanitized_test.json}"
MBPP_SIG_OUT="${DATA_DIR}/mbpp_sanitized_test_with_signature.json"

cd "${PROJECT_ROOT}"
mkdir -p "${DATA_DIR}" "${PREDICT_DIR}" "${EVAL_DIR}" "${ANALYSIS_DIR}"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== [1/4] Prepare MBPP eval prompts with signatures =========="
echo "source (read-only): ${MBPP_SOURCE}"
echo "output:             ${MBPP_SIG_OUT}"
"${PYTHON_BIN}" sft/scripts_cgh/prepare_mbpp_with_signature.py \
  --source "${MBPP_SOURCE}" \
  --output "${MBPP_SIG_OUT}"

"${PYTHON_BIN}" - <<PY
import json
from pathlib import Path
info_path = Path("${DATA_DIR}") / "dataset_info.json"
info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
info["mbpp_sanitized_test_with_signature"] = {
    "file_name": "mbpp_sanitized_test_with_signature.json"
}
info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Updated {info_path}")
PY

echo "========== [2/4] Predict with Full SFT (weights unchanged) =========="
GPU_ID="${GPU_ID}" bash "${SCRIPT_DIR}/predict.sh"

echo "========== [3/4] Execute MBPP evaluation =========="
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
"${PYTHON_BIN}" sft/scripts_cgh/analyze_errors.py \
  --cases "${EVAL_DIR}/mbpp_cases.jsonl" \
  --metrics "${EVAL_DIR}/mbpp_metrics.json" \
  --output_dir "${ANALYSIS_DIR}" \
  --tag "${TAG}"

echo ""
echo "Done (inference-only signature)."
echo "  model (read-only): sft/outputs/qwen15_code_full_sft"
echo "  predictions:       ${PREDICT_DIR}/generated_predictions.jsonl"
echo "  metrics:           ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:            ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
