#!/usr/bin/env bash
# 功能: 汇总全部 run 生成实验报告与 HTML
# 输入: state/、manifest
# 输出: reports/ 下 md 与 html
# 生成 Markdown / JSON / HTML 报告
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

cd_project_root
log_master "[03_report] 生成报告"

"${PYTHON_BIN}" "${SCRIPT_DIR}/generate_report.py" \
  --exp-dir "${EXP_DIR}" \
  --baseline-metrics "sft/outputs/eval_mbpp/mbpp_metrics.json" \
  --baseline-train "sft/outputs/qwen15_code_full_sft/train_results.json"

"${PYTHON_BIN}" "${SCRIPT_DIR}/gen_results_html.py" || true

log_master "[03_report] 完成 -> ${REPORTS_DIR}/experiment_report.md"
echo "  Markdown: ${REPORTS_DIR}/experiment_report.md"
echo "  HTML:     ${REPORTS_DIR}/results.html"
echo "  验收页:   ${REPORTS_DIR}/lora2_acceptance_dashboard.html"
