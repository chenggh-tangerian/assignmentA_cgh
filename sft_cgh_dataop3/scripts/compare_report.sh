#!/usr/bin/env bash
# Summarize DPO-protocol eval vs baselines (read-only on other dirs).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${MODULE_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

export MODULE_DIR PROJECT_ROOT
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

MODULE = Path(os.environ["MODULE_DIR"])
ROOT = Path(os.environ["PROJECT_ROOT"])

def load(p):
    p = Path(p)
    if not p.exists():
        return None
    return json.loads(p.read_text())

rows = [
    ("dataop3 (DPO eval)", MODULE / "outputs/eval_dpo/mbpp_metrics.json"),
    ("dataop3 (LLaMA sig)", MODULE / "outputs/eval/mbpp_metrics.json"),
    ("baseline Full SFT (DPO eval)", ROOT / "dpo/outputs/eval_sft_base/mbpp_metrics.json"),
    ("baseline + infer signature", ROOT / "sft/infer_signature_cgh/outputs/eval/mbpp_metrics.json"),
    ("dataop v1 HQ (LLaMA sig)", ROOT / "sft_cgh_dataop/outputs/eval/mbpp_metrics.json"),
]

lines = ["# dataop3 评测对比", "", "| 设置 | pass@1 | 语法 | 通过题数 |", "|------|--------|------|----------|"]
for name, path in rows:
    m = load(path)
    if not m:
        lines.append(f"| {name} | - | - | - |")
        continue
    p1 = m.get("pass_at_1", 0)
    syn = m.get("syntax_pass_rate", 0)
    passed = m.get("passed_tasks", "?")
    lines.append(f"| {name} | {p1:.2%} | {syn:.2%} | {passed}/257 |")

out = MODULE / "outputs/eval_dpo/compare_report.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out.read_text())
PY
