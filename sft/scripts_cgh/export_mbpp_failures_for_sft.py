#!/usr/bin/env python3
"""
功能: 从 MBPP 失败样例导出可加入 SFT 的增强数据（用参考答案作 output）。

输入:  --cases / --enriched  mbpp_cases 或带 error_category 的 jsonl
输出:  --output  SFT JSON (默认 sft/data_cgh/mbpp_failure_augment_sft.json)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = SCRIPT_DIR.parent / "outputs_cgh" / "eval_sft_with_signature" / "mbpp_cases.jsonl"
DEFAULT_OUTPUT = SCRIPT_DIR.parent / "data_cgh" / "mbpp_failure_augment_sft.json"

PRIORITY_CATEGORIES = (
    "partial_pass",
    "assertion_failure",
    "type_error",
    "boundary_error",
)


def load_cases(path: Path) -> list[dict]:
    """读取 cases jsonl。"""
    cases = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def main() -> None:
    """按错误类别筛选失败题，导出 instruction/output。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--enriched", type=Path, default=None, help="error_cases_enriched jsonl with error_category")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--categories",
        nargs="*",
        default=list(PRIORITY_CATEGORIES),
        help="error_category values to export",
    )
    args = parser.parse_args()

    if args.enriched and args.enriched.exists():
        cases = load_cases(args.enriched)
        cat_key = "error_category"
    elif args.cases.exists():
        cases = load_cases(args.cases)
        cat_key = None
    else:
        raise FileNotFoundError(f"No cases file: {args.cases}")

    exported = []
    for case in cases:
        if case.get("passed"):
            continue

        category = case.get(cat_key, "") if cat_key else ""
        if cat_key and category not in args.categories:
            # fallback: partial pass without enriched file
            if category:
                continue
            passed_tests = int(case.get("passed_tests", 0) or 0)
            total_tests = int(case.get("total_tests", 0) or 0)
            if passed_tests <= 0:
                category = "assertion_failure"
            elif passed_tests < total_tests:
                category = "partial_pass"
            else:
                continue
            if category not in args.categories:
                continue

        instruction = case.get("prompt") or case.get("instruction") or ""
        reference = case.get("reference_code") or case.get("label") or ""
        if not instruction or not reference:
            continue

        exported.append(
            {
                "instruction": instruction,
                "input": "",
                "output": reference,
                "task_id": case.get("task_id"),
                "source_category": category or "unknown",
                "model_code": case.get("code", ""),
                "passed_tests": case.get("passed_tests"),
                "total_tests": case.get("total_tests"),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(exported, f, ensure_ascii=False, indent=2)
        f.write("\n")

    counter = Counter(item["source_category"] for item in exported)
    print(f"Exported {len(exported)} failure cases -> {args.output}")
    for cat, count in counter.most_common():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
