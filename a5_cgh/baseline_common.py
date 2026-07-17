"""Greedy / CoT 单路径基线共用：生成、token 成本、timing 汇总。

输入 / 输出（函数契约）
------------------------
generate_single_path_completions(rows, rendered_prompts, tokenizer, model, ...)
    入：MBPP 行列表 + 已渲染 prompt 列表 + 已加载模型
    出：(generations, timing)
        generations: [{task_id, prompt, completion, code, *tokens}, ...]
        timing: {model_load_seconds, generation_seconds, num_generations}

summarize_single_path_token_cost(cases, method=..., prices...) -> dict
    入：含 input/output/total_tokens 的 cases
    出：写入 metrics['token_cost'] / token_cost.json 的汇总字典

summarize_single_path_timing(...) -> dict
    入：各阶段秒数与题数
    出：写入 metrics['timing'] / timing.json 的汇总字典

build_per_task_token_records(cases) -> list[dict]
    入：cases；出：逐题 token 行，写 mbpp_token_cost_per_task_{method}.jsonl

本文件无直接读写磁盘，由 mbpp_eval_baseline.py 调用后落盘。
"""

from __future__ import annotations

import time
from typing import Any, Callable

from token_stats import count_sample_generation_tokens


def summarize_single_path_token_cost(
    cases: list[dict[str, Any]],
    *,
    method: str,
    input_price_per_1m: float = 0.0,
    output_price_per_1m: float = 0.0,
) -> dict[str, Any]:
    """汇总 Greedy/CoT 全量任务的 input/output token 及可选成本。"""
    num_tasks = len(cases)
    input_tokens = sum(int(case.get("input_tokens", 0)) for case in cases)
    output_tokens = sum(int(case.get("output_tokens", 0)) for case in cases)
    total_tokens = input_tokens + output_tokens

    generation = {
        "num_generations": num_tasks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "avg_input_tokens_per_task": input_tokens / num_tasks if num_tasks else 0.0,
        "avg_output_tokens_per_task": output_tokens / num_tasks if num_tasks else 0.0,
        "avg_total_tokens_per_task": total_tokens / num_tasks if num_tasks else 0.0,
    }

    estimated_cost_usd = None
    if input_price_per_1m > 0.0 or output_price_per_1m > 0.0:
        input_cost = input_tokens * input_price_per_1m / 1_000_000
        output_cost = output_tokens * output_price_per_1m / 1_000_000
        estimated_cost_usd = {
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "input_price_per_1m_tokens": input_price_per_1m,
            "output_price_per_1m_tokens": output_price_per_1m,
        }

    return {
        "method": method,
        "num_tasks": num_tasks,
        "num_generations": num_tasks,
        "generation": generation,
        "per_task_avg_generation": {
            "num_generations": 1.0,
            "input_tokens": generation["avg_input_tokens_per_task"],
            "output_tokens": generation["avg_output_tokens_per_task"],
            "total_tokens": generation["avg_total_tokens_per_task"],
            "avg_input_tokens_per_task": generation["avg_input_tokens_per_task"],
            "avg_output_tokens_per_task": generation["avg_output_tokens_per_task"],
            "avg_total_tokens_per_task": generation["avg_total_tokens_per_task"],
        },
        "final_answer": generation,
        "estimated_cost_usd": estimated_cost_usd,
        "note": "Single-path greedy decode: one model.generate() call per task.",
    }


def summarize_single_path_timing(
    *,
    method: str,
    num_tasks: int,
    total_seconds: float,
    model_load_seconds: float,
    generation_seconds: float,
    num_generations: int,
    scoring_seconds: float,
    skipped_generation: bool = False,
) -> dict[str, Any]:
    """汇总加载 / 生成 / 判题各阶段耗时。"""
    return {
        "method": method,
        "num_tasks": num_tasks,
        "skipped_generation": skipped_generation,
        "total_seconds": round(total_seconds, 3),
        "accounted_seconds": round(
            model_load_seconds + generation_seconds + scoring_seconds,
            3,
        ),
        "unaccounted_seconds": round(
            total_seconds - model_load_seconds - generation_seconds - scoring_seconds,
            3,
        ),
        "model_load_seconds": round(model_load_seconds, 3),
        "generation_seconds": round(generation_seconds, 3),
        "scoring_seconds": round(scoring_seconds, 3),
        "avg_seconds_per_task": round(total_seconds / num_tasks, 4) if num_tasks else 0.0,
        "phases": {
            "generation": {
                "seconds": round(generation_seconds, 3),
                "num_generations": num_generations,
                "seconds_per_generation": (
                    round(generation_seconds / num_generations, 4) if num_generations else 0.0
                ),
                "seconds_per_task": round(generation_seconds / num_tasks, 4) if num_tasks else 0.0,
            },
            "scoring": {
                "seconds": round(scoring_seconds, 3),
                "num_items": num_tasks,
                "seconds_per_item": round(scoring_seconds / num_tasks, 4) if num_tasks else 0.0,
            },
        },
        "note": (
            "total_seconds is end-to-end wall time. "
            "generation_seconds sums model.generate() calls. "
            "scoring_seconds covers subprocess assert execution."
        ),
    }


def build_per_task_token_records(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """导出逐题 token 记录（每题一次 generate）。"""
    rows = []
    for case in cases:
        rows.append(
            {
                "task_id": int(case["task_id"]),
                "num_generations": 1,
                "generation": {
                    "input_tokens": int(case.get("input_tokens", 0)),
                    "output_tokens": int(case.get("output_tokens", 0)),
                    "total_tokens": int(case.get("total_tokens", 0)),
                },
            }
        )
    return rows


def generate_single_path_completions(
    rows: list[dict[str, Any]],
    rendered_prompts: list[str],
    *,
    tokenizer: Any,
    model: Any,
    torch: Any,
    batch_size: int,
    max_new_tokens: int,
    extract_code_fn: Callable[[str], str],
    row_prompt_fn: Callable[[dict[str, Any]], str],
    model_load_seconds: float = 0.0,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """按 batch 做 temperature=0 单路径生成，并用 extract_code_fn 抽代码。"""
    generations: list[dict[str, Any]] = []
    generation_seconds = 0.0

    for start in range(0, len(rendered_prompts), batch_size):
        batch_prompts = rendered_prompts[start : start + batch_size]
        batch_rows = rows[start : start + batch_size]
        inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True)
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        prompt_width = inputs["input_ids"].shape[1]
        attention_mask = inputs.get("attention_mask")

        gen_start = time.perf_counter()
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=1,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        generation_seconds += time.perf_counter() - gen_start

        for offset, output in enumerate(output_ids):
            completion = tokenizer.decode(output[prompt_width:], skip_special_tokens=True)
            row = batch_rows[offset]
            code = extract_code_fn(completion)
            token_stats = count_sample_generation_tokens(
                attention_mask_row=attention_mask[offset],
                output_ids_row=output,
                prompt_width=prompt_width,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
            generations.append(
                {
                    "task_id": int(row["task_id"]),
                    "prompt": row_prompt_fn(row),
                    "completion": completion,
                    "code": code,
                    "reference_code": row.get("code", ""),
                    **token_stats,
                }
            )

        print(f"Generated {len(generations)} / {len(rendered_prompts)}", flush=True)

    timing = {
        "model_load_seconds": model_load_seconds,
        "generation_seconds": generation_seconds,
        "num_generations": len(generations),
    }
    return generations, timing
