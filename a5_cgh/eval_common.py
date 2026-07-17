"""a5_cgh 评测脚本共用的路径与 tokenizer 工具。

输入 / 输出（函数契约）
------------------------
resolve_model_path(model_path) -> Path
    入：相对 assignment_A 的路径或绝对路径
    出：resolve 后的绝对 Path

load_tokenizer(model_path, trust_remote_code) -> AutoTokenizer
    入：模型目录；出：HuggingFace tokenizer
    主要给 ToT `--skip_generation` 时按文本回填 token 使用

无文件写出；被 mbpp_eval_baseline.py / mbpp_eval_tot.py 调用。
"""

from __future__ import annotations

from pathlib import Path

A5_ROOT = Path(__file__).resolve().parent
ASSIGNMENT_ROOT = A5_ROOT.parent


def resolve_model_path(model_path: Path) -> Path:
    """相对 assignment_A 根目录解析模型路径；绝对路径则直接 resolve。"""
    if model_path.is_absolute():
        return model_path.resolve()
    return (ASSIGNMENT_ROOT / model_path).resolve()


def load_tokenizer(model_path: Path, trust_remote_code: bool):
    """加载 HuggingFace tokenizer（ToT skip_generation 补算 token 时使用）。"""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=trust_remote_code)
