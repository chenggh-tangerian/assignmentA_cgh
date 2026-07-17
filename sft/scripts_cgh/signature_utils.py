"""
功能: 从参考代码抽取函数签名，并注入到 Alpaca instruction 中。

输入: 含 instruction / output 的样本行
输出: 增强后的样本；无法抽取签名时按参数决定丢弃或原样保留
"""
from __future__ import annotations

import ast
import re
from typing import Any

DEF_LINE_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(([^)]*)\)\s*:", re.MULTILINE)

SIGNATURE_SUFFIX = (
    "\n\nYou must implement the solution using exactly this function signature "
    "(keep the function name and parameter names unchanged):\n{signature}"
)


def normalize_text(value: Any) -> str:
    """统一换行并去首尾空白。"""
    return str(value or "").replace("\r\n", "\n").strip()


def extract_signature(code: str) -> str | None:
    """从代码中抽取首个 def 签名行；失败返回 None。"""
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


def build_instruction_with_signature(original: str, signature: str) -> str:
    """在原 instruction 末尾追加强制签名约束。"""
    return normalize_text(original) + SIGNATURE_SUFFIX.format(signature=signature)


def augment_row(row: dict[str, Any], *, drop_without_signature: bool = False) -> dict[str, Any] | None:
    """增强单行；无效或无可抽取签名时可返回 None。"""
    instruction = normalize_text(row.get("instruction"))
    output = normalize_text(row.get("output"))
    if not instruction or not output:
        return None

    signature = extract_signature(output)
    if not signature:
        if drop_without_signature:
            return None
        new_instruction = instruction
    else:
        new_instruction = build_instruction_with_signature(instruction, signature)

    converted = {
        "instruction": new_instruction,
        "input": normalize_text(row.get("input")),
        "output": output,
    }
    if row.get("task_id") is not None:
        converted["task_id"] = int(row["task_id"])
    return converted
