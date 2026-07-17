#!/usr/bin/env python3
"""
功能: 为 MBPP 评测集 instruction 注入参考答案中的函数签名。

输入:  --source  MBPP JSON (默认 sft/data_cgh/mbpp_sanitized_test.json)
输出:  --output  带签名的 JSON (默认 .../mbpp_sanitized_test_with_signature.json)
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = SCRIPT_DIR.parent / "data_cgh" / "mbpp_sanitized_test.json"
DEFAULT_OUTPUT = SCRIPT_DIR.parent / "data_cgh" / "mbpp_sanitized_test_with_signature.json"

DEF_LINE_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(([^)]*)\)\s*:", re.MULTILINE)

SIGNATURE_SUFFIX = (
    "\n\nYou must implement the solution using exactly this function signature "
    "(keep the function name and parameter names unchanged):\n{signature}"
)


def normalize_text(value: Any) -> str:
    """统一换行并去首尾空白。"""
    return str(value or "").replace("\r\n", "\n").strip()


def extract_signature(code: str) -> str | None:
    """从参考代码抽取函数签名。"""
    code = normalize_text(code)
    if not code:
        return None

    try:
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                args_text = ast.unparse(node.args)
                if not args_text.startswith("("):
                    args_text = f"({args_text})"
                return f"def {node.name}{args_text}:"
    except SyntaxError:
        pass

    match = DEF_LINE_RE.search(code)
    if not match:
        return None
    name, params = match.group(1), match.group(2).strip()
    if params:
        return f"def {name}({params}):"
    return f"def {name}():"


def build_instruction(original: str, signature: str) -> str:
    """拼接原题描述与签名约束。"""
    original = normalize_text(original)
    return original + SIGNATURE_SUFFIX.format(signature=signature)


def convert_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """转换单行；缺签名则丢弃。"""
    instruction = normalize_text(row.get("instruction"))
    output = normalize_text(row.get("output"))
    signature = extract_signature(output)
    if not instruction or not output or not signature:
        return None

    converted = {
        "instruction": build_instruction(instruction, signature),
        "input": normalize_text(row.get("input")),
        "output": output,
    }
    if row.get("task_id") is not None:
        converted["task_id"] = int(row["task_id"])
    return converted


def main() -> None:
    """读源 JSON，写出签名增强后的 MBPP 集。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.source.exists():
        raise FileNotFoundError(f"Missing source dataset: {args.source}")

    with args.source.open(encoding="utf-8") as f:
        rows = json.load(f)

    converted: list[dict[str, Any]] = []
    skipped = 0
    for row in rows:
        item = convert_row(row)
        if item is None:
            skipped += 1
            continue
        converted.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
        f.write("\n")

    dataset_info_path = args.output.parent / "dataset_info.json"
    dataset_info: dict[str, dict[str, str]] = {}
    if dataset_info_path.exists():
        with dataset_info_path.open(encoding="utf-8") as f:
            dataset_info = json.load(f)
    dataset_info["mbpp_sanitized_test_with_signature"] = {"file_name": args.output.name}
    with dataset_info_path.open("w", encoding="utf-8") as f:
        json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Source rows: {len(rows)}")
    print(f"Converted rows: {len(converted)}")
    print(f"Skipped rows: {skipped}")
    print(f"Wrote {args.output}")
    print(f"Updated {dataset_info_path}")
    if converted:
        print("\nExample instruction tail:")
        print(converted[0]["instruction"][-220:])


if __name__ == "__main__":
    main()
