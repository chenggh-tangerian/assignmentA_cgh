#!/usr/bin/env bash
# Predict + MBPP eval + error analysis for HQ-SFT model.
# Reuses existing evaluate/analyze scripts (read-only invocation); writes only under sft_cgh_dataop/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
SFT_DIR="${PROJECT_ROOT}/sft"
LLAMA_FACTORY_DIR="${LLAMA_FACTORY_DIR:-${PROJECT_ROOT}/LlamaFactory}"
PYTHON_BIN="${PYTHON_BIN:-/opt/conda/envs/chenggh-sft/bin/python}"
GPU_ID="${GPU_ID:-0}"
CONFIG="${CONFIG:-${MODULE_DIR}/configs/qwen15_hq_sft_predict.yaml}"

PREDICT_DIR="${MODULE_DIR}/outputs/predict"
EVAL_DIR="${MODULE_DIR}/outputs/eval"
ANALYSIS_DIR="${MODULE_DIR}/outputs/analysis"
TAG="${TAG:-hq_sft_dataop}"

# Same as other SFT scripts: source-load llamafactory via PYTHONPATH.
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-${GPU_ID}}"
export PYTHONPATH="${LLAMA_FACTORY_DIR}/src:${PYTHONPATH:-}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export WANDB_DISABLED="${WANDB_DISABLED:-true}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"

# Signature MBPP lives only under this module (read source from sft/data or reuse existing copy).
MBPP_SIG="${MODULE_DIR}/data/mbpp_sanitized_test_with_signature.json"
MBPP_SRC_READONLY="${SFT_DIR}/data/mbpp_sanitized_test.json"
MBPP_EXISTING="${SFT_DIR}/infer_signature_cgh/data/mbpp_sanitized_test_with_signature.json"
if [[ ! -f "${MBPP_SIG}" ]]; then
  mkdir -p "${MODULE_DIR}/data"
  if [[ -f "${MBPP_EXISTING}" ]]; then
    echo "[predict] copy signature MBPP (read-only source) -> ${MBPP_SIG}"
    cp "${MBPP_EXISTING}" "${MBPP_SIG}"
  else
    echo "[predict] build signature MBPP into module data ..."
    "${PYTHON_BIN}" "${SFT_DIR}/scripts_cgh/prepare_mbpp_with_signature.py" \
      --source "${MBPP_SRC_READONLY}" \
      --output "${MBPP_SIG}"
  fi
fi
"${PYTHON_BIN}" - <<PY
import json
from pathlib import Path
info_path = Path("${MODULE_DIR}/data/dataset_info.json")
info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
info["mbpp_sanitized_test_with_signature"] = {
    "file_name": "mbpp_sanitized_test_with_signature.json"
}
info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Updated {info_path}")
PY

cd "${PROJECT_ROOT}"
mkdir -p "${PREDICT_DIR}" "${EVAL_DIR}" "${ANALYSIS_DIR}"

MODEL_DIR="${MODULE_DIR}/outputs/train/qwen15_hq_full_sft"
if [[ ! -d "${MODEL_DIR}" ]]; then
  echo "Missing trained model: ${MODEL_DIR}"
  echo "Run: bash ${SCRIPT_DIR}/train.sh"
  exit 1
fi

echo "[predict] GPU=${GPU_ID}"
"${PYTHON_BIN}" -m llamafactory.cli train "${CONFIG}"

echo "[eval] MBPP execution"
"${PYTHON_BIN}" "${SFT_DIR}/scripts/evaluate_code_predictions.py" \
  --predictions "${PREDICT_DIR}/generated_predictions.jsonl" \
  --mbpp_dir "${MBPP_DIR:-/root/siton-tmp/mbpp}" \
  --config "${MBPP_CONFIG:-sanitized}" \
  --split "${MBPP_SPLIT:-test}" \
  --output_dir "${EVAL_DIR}" \
  --case_limit "${CASE_LIMIT:-257}" \
  --limit "${LIMIT:-0}" \
  --test_timeout "${TEST_TIMEOUT:-5.0}" \
  --memory_mb "${MEMORY_MB:-1024}"

echo "[analysis] error categories"
"${PYTHON_BIN}" "${SFT_DIR}/scripts_cgh/analyze_errors.py" \
  --cases "${EVAL_DIR}/mbpp_cases.jsonl" \
  --metrics "${EVAL_DIR}/mbpp_metrics.json" \
  --output_dir "${ANALYSIS_DIR}" \
  --tag "${TAG}"

echo "[predict] done"
echo "  metrics: ${EVAL_DIR}/mbpp_metrics.json"
echo "  report:  ${ANALYSIS_DIR}/error_analysis_${TAG}.md"
