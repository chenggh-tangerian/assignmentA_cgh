"""Token 计数工具：供 Greedy / CoT / ToT 统计 input/output tokens。

输入 / 输出（函数契约）
------------------------
count_sample_generation_tokens(attention_mask_row, output_ids_row, prompt_width, ...)
    入：一次 model.generate 的 mask / ids
    出：{input_tokens, output_tokens, total_tokens}

count_text_tokens(tokenizer, prompt, completion, apply_chat_template_fn=None)
    入：已保存的 prompt/completion 文本（可选再套 chat_template）
    出：同上 token 三元组（用于 skip_generation 补算）

无文件 I/O；被 baseline_common / tree_of_thoughts 调用。
"""

from __future__ import annotations

from typing import Any


def count_sample_generation_tokens(
    *,
    attention_mask_row: Any,
    output_ids_row: Any,
    prompt_width: int,
    pad_token_id: int | None,
    eos_token_id: int | None,
) -> dict[str, int]:
    """从一次 generate 的 attention_mask / output_ids 统计本样本 token 数。"""
    input_tokens = int(attention_mask_row.sum().item())

    output_tokens = 0
    for token_id in output_ids_row[prompt_width:]:
        tid = int(token_id.item())
        if eos_token_id is not None and tid == eos_token_id:
            break
        if pad_token_id is not None and tid == pad_token_id:
            continue
        output_tokens += 1

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def count_text_tokens(
    tokenizer: Any,
    prompt: str,
    completion: str,
    *,
    apply_chat_template_fn=None,
) -> dict[str, int]:
    """从已保存的 prompt/completion 文本估计 token 数（用于 skip_generation 重跑）。"""
    prompt_text = str(prompt or "")
    if apply_chat_template_fn is not None:
        prompt_text = apply_chat_template_fn(tokenizer, prompt_text)
    completion_text = str(completion or "")
    input_tokens = len(tokenizer.encode(prompt_text, add_special_tokens=False))
    output_tokens = len(tokenizer.encode(completion_text, add_special_tokens=False))
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
