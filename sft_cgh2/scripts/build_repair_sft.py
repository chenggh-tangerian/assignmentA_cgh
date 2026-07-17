#!/usr/bin/env python3
"""从 MBPP 失败评测 case 构建代码修复式 SFT 数据。

输入:
  --cases  MBPP 评测结果 JSONL（默认 r8_tqv_q4/eval/mbpp_cases.jsonl）
           每行含 prompt / code|predict / test_results / reference_code / passed 等字段

输出:
  <output-dir>/repair_sft_train.json   训练集（Alpaca 三字段 + 元信息）
  <output-dir>/repair_sft_valid.json   验证集
  <output-dir>/repair_sft_all.json     全部样本
  <output-dir>/dataset_info.json        LLaMA-Factory 数据集注册信息

样本映射: 题目 + 错误代码 + 失败测试反馈 -> 参考修复代码
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CASES = Path("sft/lora2_exp_cgh/outputs/r8_tqv_q4/eval/mbpp_cases.jsonl")
DEFAULT_OUTPUT_DIR = Path("sft_cgh2/data")
REPAIR_INSTRUCTION = (
    "Fix the buggy Python code so that it satisfies the programming task and "
    "passes the failing tests. Return only the corrected Python code."
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数：数据路径、划分比例、反馈截断长度等。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="MBPP eval cases JSONL.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-feedback-chars", type=int, default=2400)
    parser.add_argument("--max-failed-tests", type=int, default=3)
    parser.add_argument("--include-passing", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """按行读取 JSONL，跳过空行，解析失败则报错。"""
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no} of {path}") from exc
    return rows


def clean_text(value: Any) -> str:
    """把任意值转成干净字符串：去空、统一换行。"""
    return str(value or "").replace("\r\n", "\n").strip()


def truncate_text(text: str, limit: int) -> str:
    """按字符上限截断文本，末尾加标记，避免 prompt 过长。"""
    if limit <= 0 or len(text) <= limit:
        return text
    keep = max(0, limit - 80)
    return text[:keep].rstrip() + "\n... [truncated for SFT prompt length]"


def classify_error(case: dict[str, Any]) -> str:
    """根据 syntax_ok / stderr 粗分错误类型（name_error、assertion_failure 等）。"""
    if case.get("syntax_ok") is False:
        return "syntax_error"

    stderr = "\n".join(clean_text(result.get("stderr")) for result in case.get("test_results", []))
    if "NameError" in stderr:
        return "name_error"
    if "AssertionError" in stderr:
        return "assertion_failure"
    if "TypeError" in stderr:
        return "type_error"
    if "IndexError" in stderr:
        return "index_error"
    if "ValueError" in stderr:
        return "value_error"
    if stderr.strip():
        return "runtime_error"
    return "failed"


def compact_traceback(stderr: str) -> str:
    """压缩 traceback，只保留 assert / Error / File 行，最多 8 行。"""
    stderr = clean_text(stderr)
    if not stderr:
        return ""

    lines = stderr.splitlines()
    useful: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped.startswith("assert ")
            or stripped.endswith("Error")
            or "Error:" in stripped
            or "NameError:" in stripped
            or "TypeError:" in stripped
            or "AssertionError" in stripped
            or "SyntaxError:" in stripped
            or re.match(r"File .*, line \d+", stripped)
        ):
            useful.append(line)

    return "\n".join(useful[-8:]) if useful else stderr


def format_feedback(case: dict[str, Any], max_failed_tests: int, max_feedback_chars: int) -> str:
    """把失败测例整理成可读反馈文本：通过率摘要 + 若干条 stdout/stderr。"""
    results = case.get("test_results") or []
    failed = [result for result in results if not result.get("passed")]
    selected = failed[:max_failed_tests] if failed else results[:max_failed_tests]

    chunks: list[str] = []
    for idx, result in enumerate(selected, start=1):
        error_type = clean_text(result.get("error_type")) or "unknown"
        stdout = clean_text(result.get("stdout"))
        stderr = compact_traceback(clean_text(result.get("stderr")))

        parts = [f"Test {idx}: {error_type}"]
        if stdout:
            parts.append("stdout:\n" + stdout)
        if stderr:
            parts.append("stderr:\n" + stderr)
        chunks.append("\n".join(parts))

    if not chunks:
        chunks.append(
            "The candidate did not pass the evaluator, but no detailed traceback was available."
        )

    summary = (
        f"Passed {case.get('passed_tests', 0)} / {case.get('total_tests', 0)} tests. "
        f"Error category: {classify_error(case)}."
    )
    feedback = summary + "\n\n" + "\n\n---\n\n".join(chunks)
    return truncate_text(feedback, max_feedback_chars)


def build_input(case: dict[str, Any], args: argparse.Namespace) -> str:
    """拼 Alpaca 的 input 字段：Problem + Buggy Code + Failing Tests。"""
    problem = clean_text(case.get("prompt") or case.get("instruction"))
    buggy_code = clean_text(case.get("code") or case.get("predict"))
    feedback = format_feedback(case, args.max_failed_tests, args.max_feedback_chars)

    return (
        "### Problem\n"
        f"{problem}\n\n"
        "### Buggy Code\n"
        "```python\n"
        f"{buggy_code}\n"
        "```\n\n"
        "### Failing Tests / Error Messages\n"
        f"{feedback}"
    )


def build_sample(case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any] | None:
    """把一条评测 case 转成修复 SFT 样本；缺字段则返回 None。"""
    problem = clean_text(case.get("prompt") or case.get("instruction"))
    buggy_code = clean_text(case.get("code") or case.get("predict"))
    fixed_code = clean_text(case.get("reference_code") or case.get("label") or case.get("output"))
    if not problem or not buggy_code or not fixed_code:
        return None

    return {
        "instruction": REPAIR_INSTRUCTION,
        "input": build_input(case, args),
        "output": fixed_code,
        "task_id": case.get("task_id"),
        "source": str(args.cases),
        "error_category": classify_error(case),
        "passed_tests": case.get("passed_tests"),
        "total_tests": case.get("total_tests"),
    }


def split_samples(
    samples: list[dict[str, Any]], valid_ratio: float, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """按比例随机划分 train / valid，保证可复现。"""
    if not samples:
        return [], []

    shuffled = list(samples)
    random.Random(seed).shuffle(shuffled)
    valid_size = int(round(len(shuffled) * valid_ratio))
    if len(shuffled) > 1:
        valid_size = min(max(valid_size, 1), len(shuffled) - 1)
    else:
        valid_size = 0

    valid = shuffled[:valid_size]
    train = shuffled[valid_size:]
    return train, valid


def write_json(path: Path, data: Any) -> None:
    """把数据写成缩进 JSON 文件，必要时创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """主流程：读 cases → 筛选失败样本 → 建样本 → 划分 → 写出四份文件。"""
    args = parse_args()
    if not args.cases.exists():
        raise FileNotFoundError(f"Cases file not found: {args.cases}")
    if not 0 <= args.valid_ratio < 1:
        raise ValueError("--valid-ratio must be in [0, 1)")

    rows = load_jsonl(args.cases)
    selected = [row for row in rows if args.include_passing or not row.get("passed")]
    samples = [sample for row in selected if (sample := build_sample(row, args))]
    train, valid = split_samples(samples, args.valid_ratio, args.seed)

    out = args.output_dir
    write_json(out / "repair_sft_train.json", train)
    write_json(out / "repair_sft_valid.json", valid)
    write_json(out / "repair_sft_all.json", samples)
    write_json(
        out / "dataset_info.json",
        {
            "repair_sft_train": {"file_name": "repair_sft_train.json"},
            "repair_sft_valid": {"file_name": "repair_sft_valid.json"},
            "repair_sft_all": {"file_name": "repair_sft_all.json"},
        },
    )

    counts = Counter(sample["error_category"] for sample in samples)
    print(f"Loaded cases: {len(rows)}")
    print(f"Exported repair samples: {len(samples)}")
    print(f"Train / valid: {len(train)} / {len(valid)}")
    print(f"Output dir: {out}")
    for category, count in counts.most_common():
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
