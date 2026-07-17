"""Tree of Thoughts 搜索与指标辅助（由 mbpp_eval_tot.py 驱动）。

两阶段搜索
----------
1. 生成 branch_factor 条 thought → 打分剪枝到 beam_width
2. 每个保留 thought 扩展 branch_factor 条 code → verifier 选优

输入 / 输出（主要函数契约）
----------------------------
build_thought_prompt / build_value_prompt / build_code_prompt
    入：MBPP 官方风格 original_prompt（可含 [BEGIN]）与 thought 文本
    出：各阶段发给模型的字符串 prompt

batch_generate(prompts, tokenizer, model, ...) -> (completions, token_stats_list, elapsed)
    入：一批 prompt；出：回复列表、逐条 token、墙钟秒数

prune_thoughts(thoughts, beam_width) -> list
    入：带 value_score 的 thoughts；出：保留的 top-k

select_best_code(candidates) -> (selected, selection_meta)
    入：已打分代码候选；出：最优候选 + 选优说明

summarize_tot_token_cost(task_records, final_cases=..., ...) -> dict
    入：整棵树的 task_records；出：token_cost.json 结构

summarize_tot_timing(...) -> dict
    入：各阶段秒数；出：timing.json 结构

build_per_task_tot_records(task_records) -> list[dict]
    入：task_records；出：逐题 token / 候选规模行

本文件不直接写磁盘；落盘由 mbpp_eval_tot.py 完成。
"""

from __future__ import annotations

import re
import time
from typing import Any

from token_stats import count_sample_generation_tokens, count_text_tokens


THOUGHT_INSTRUCTION = (
    "You are planning a Python solution. Write a short step-by-step approach "
    "(3-6 bullet points). Focus on algorithm, edge cases, and the function "
    "signature implied by the tests. Do NOT write code yet."
)

VALUE_INSTRUCTION = (
    "Rate the following solution plan for the coding task on a scale from 0 to 10. "
    "Consider correctness, completeness, and match to the tests. "
    "Reply with a single number only."
)

CODE_FROM_THOUGHT_INSTRUCTION = (
    "Implement the Python solution following the plan below. "
    "Write complete, runnable code that passes the tests."
)


def clean_text(value: Any) -> str:
    """统一换行并 strip。"""
    return str(value or "").replace("\r\n", "\n").strip()


def strip_begin_marker(prompt: str) -> str:
    """去掉官方 MBPP prompt 末尾的 [BEGIN]，便于改写成 thought/code prompt。"""
    text = clean_text(prompt)
    if text.endswith("[BEGIN]"):
        return text[: -len("[BEGIN]")].rstrip()
    return text


def build_thought_prompt(*, original_prompt: str) -> str:
    """构造「只写计划、不写代码」的 thought 阶段 prompt。"""
    base = strip_begin_marker(original_prompt)
    return (
        f"{base}\n\n"
        f"{THOUGHT_INSTRUCTION}\n\n"
        "### Plan\n"
    )


def build_value_prompt(*, task_prompt: str, thought: str) -> str:
    """构造对某个 thought 打 0–10 分的 value 阶段 prompt。"""
    return (
        f"{VALUE_INSTRUCTION}\n\n"
        "### Task\n"
        f"{clean_text(task_prompt)}\n\n"
        "### Plan\n"
        f"{clean_text(thought)}\n\n"
        "### Score\n"
    )


def build_code_prompt(*, original_prompt: str, thought: str) -> str:
    """在保留的 thought 指导下构造 code 扩展 prompt（以 [BEGIN] 结尾）。"""
    base = strip_begin_marker(original_prompt)
    return (
        f"{base}\n\n"
        f"{CODE_FROM_THOUGHT_INSTRUCTION}\n\n"
        "### Plan\n"
        f"{clean_text(thought)}\n\n"
        "Write the Python code.\n"
        "[BEGIN]\n"
    )


def parse_value_score(text: str) -> float:
    """Extract a 0-10 numeric score from model output; fallback to heuristic."""
    cleaned = clean_text(text)
    match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)(?!\d)", cleaned)
    if match:
        value = float(match.group(1))
        if value > 10.0 and value <= 100.0:
            value = value / 10.0
        return max(0.0, min(10.0, value))
    return heuristic_thought_score(cleaned)


def heuristic_thought_score(thought: str) -> float:
    """Lightweight prior when LLM value scoring is disabled or unparsable."""
    text = clean_text(thought)
    if not text:
        return 0.0
    score = 3.0
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    score += min(3.0, 0.6 * len(lines))
    keywords = (
        "function",
        "return",
        "edge",
        "case",
        "test",
        "loop",
        "list",
        "string",
        "dict",
        "sort",
        "count",
        "algorithm",
        "step",
    )
    lowered = text.lower()
    score += min(2.0, 0.35 * sum(1 for key in keywords if key in lowered))
    if "```" in text or "def " in text:
        score -= 1.5  # prefer plans without premature code dumps
    if len(text) < 40:
        score -= 1.0
    if len(text) > 1200:
        score -= 0.5
    return max(0.0, min(10.0, score))


def make_node_record(
    *,
    task_id: int,
    node_id: str,
    depth: int,
    phase: str,
    parent_id: str | None,
    prompt: str,
    completion: str,
    thought: str = "",
    code: str = "",
    value_score: float | None = None,
    token_stats: dict[str, int] | None = None,
    elapsed_seconds: float = 0.0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """组装 ToT 树上的一个节点记录（thought / value / code）。"""
    token_stats = token_stats or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    record = {
        "task_id": task_id,
        "node_id": node_id,
        "parent_id": parent_id,
        "depth": depth,
        "phase": phase,
        "prompt": prompt,
        "completion": completion,
        "thought": thought,
        "code": code,
        "value_score": value_score,
        "input_tokens": int(token_stats.get("input_tokens", 0)),
        "output_tokens": int(token_stats.get("output_tokens", 0)),
        "total_tokens": int(token_stats.get("total_tokens", 0)),
        "elapsed_seconds": round(elapsed_seconds, 4),
    }
    if extra:
        record.update(extra)
    return record


def batch_generate(
    prompts: list[str],
    *,
    tokenizer: Any,
    model: Any,
    torch: Any,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    greedy: bool,
    apply_chat_template_fn,
) -> tuple[list[str], list[dict[str, int]], float]:
    """批量调用 model.generate，返回 completions、逐条 token 统计与耗时。"""
    if not prompts:
        return [], [], 0.0

    rendered = [apply_chat_template_fn(tokenizer, prompt) for prompt in prompts]
    inputs = tokenizer(rendered, return_tensors="pt", padding=True, truncation=True)
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    prompt_width = inputs["input_ids"].shape[1]
    attention_mask = inputs.get("attention_mask")

    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": not greedy,
        "num_beams": 1,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if not greedy:
        generation_kwargs["temperature"] = temperature
        generation_kwargs["top_p"] = top_p

    start = time.perf_counter()
    with torch.no_grad():
        output_ids = model.generate(**inputs, **generation_kwargs)
    elapsed = time.perf_counter() - start

    completions: list[str] = []
    token_stats_list: list[dict[str, int]] = []
    for offset, output in enumerate(output_ids):
        completion = tokenizer.decode(output[prompt_width:], skip_special_tokens=True)
        token_stats = count_sample_generation_tokens(
            attention_mask_row=attention_mask[offset],
            output_ids_row=output,
            prompt_width=prompt_width,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        completions.append(completion)
        token_stats_list.append(token_stats)
    return completions, token_stats_list, elapsed


def prune_thoughts(
    thoughts: list[dict[str, Any]],
    beam_width: int,
) -> list[dict[str, Any]]:
    """按 value_score 降序剪枝，保留 beam_width 条 thought。"""
    ranked = sorted(
        thoughts,
        key=lambda item: (
            -float(item.get("value_score") or 0.0),
            int(item.get("branch_index", 0)),
        ),
    )
    return ranked[: max(1, beam_width)]


def code_selection_key(sample: dict[str, Any]) -> tuple[Any, ...]:
    """代码选优排序键：优先全过测试，其次过测数 / 语法 / verifier / 父节点分数。"""
    return (
        0 if sample.get("passed") else 1,
        -int(sample.get("passed_tests", 0)),
        0 if sample.get("syntax_ok") else 1,
        -float(sample.get("verifier_score", 0.0)),
        -float(sample.get("parent_value_score") or 0.0),
        int(sample.get("branch_index", 0)),
    )


def select_best_code(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """从代码候选中选最优一条，并返回选优元信息。"""
    if not candidates:
        raise ValueError("Cannot select from empty ToT code candidates")
    ranked = sorted(candidates, key=code_selection_key)
    selected = ranked[0]
    meta = {
        "strategy": "tot_beam",
        "selected_node_id": selected.get("node_id"),
        "selected_parent_id": selected.get("parent_id"),
        "num_candidates": len(candidates),
        "num_passed_candidates": sum(1 for item in candidates if item.get("passed")),
        "selected_value_score": selected.get("parent_value_score"),
        "selected_verifier_score": selected.get("verifier_score"),
        "candidate_scores": [
            {
                "node_id": item.get("node_id"),
                "parent_id": item.get("parent_id"),
                "passed": item.get("passed"),
                "passed_tests": item.get("passed_tests"),
                "syntax_ok": item.get("syntax_ok"),
                "verifier_score": item.get("verifier_score"),
                "parent_value_score": item.get("parent_value_score"),
            }
            for item in ranked
        ],
    }
    return selected, meta


def summarize_task_nodes(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总单题所有节点的 token 与按 phase 分组统计。"""
    input_tokens = sum(int(item.get("input_tokens", 0)) for item in nodes)
    output_tokens = sum(int(item.get("output_tokens", 0)) for item in nodes)
    total_tokens = sum(int(item.get("total_tokens", 0)) for item in nodes)
    by_phase: dict[str, dict[str, Any]] = {}
    for item in nodes:
        phase = str(item.get("phase", "unknown"))
        bucket = by_phase.setdefault(
            phase,
            {"count": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "seconds": 0.0},
        )
        bucket["count"] += 1
        bucket["input_tokens"] += int(item.get("input_tokens", 0))
        bucket["output_tokens"] += int(item.get("output_tokens", 0))
        bucket["total_tokens"] += int(item.get("total_tokens", 0))
        bucket["seconds"] += float(item.get("elapsed_seconds", 0.0))
    return {
        "num_generations": len(nodes),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "by_phase": by_phase,
    }


def summarize_tot_token_cost(
    task_records: list[dict[str, Any]],
    *,
    final_cases: list[dict[str, Any]] | None = None,
    branch_factor: int,
    beam_width: int,
    depth: int,
    input_price_per_1m: float = 0.0,
    output_price_per_1m: float = 0.0,
) -> dict[str, Any]:
    """汇总 ToT 全量题的 generation / by_phase / final_answer token 成本。"""
    num_tasks = len(task_records)
    if num_tasks == 0:
        return {
            "method": "tree_of_thoughts",
            "num_tasks": 0,
            "branch_factor": branch_factor,
            "beam_width": beam_width,
            "depth": depth,
            "generation": _empty_block(),
            "per_task_avg_generation": _empty_block(),
            "by_phase": {},
            "final_answer": None,
            "estimated_cost_usd": None,
        }

    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "num_generations": 0}
    phase_totals: dict[str, dict[str, Any]] = {}
    for record in task_records:
        stats = record.get("token_stats") or summarize_task_nodes(record.get("nodes", []))
        totals["input_tokens"] += int(stats.get("input_tokens", 0))
        totals["output_tokens"] += int(stats.get("output_tokens", 0))
        totals["total_tokens"] += int(stats.get("total_tokens", 0))
        totals["num_generations"] += int(stats.get("num_generations", 0))
        for phase, bucket in (stats.get("by_phase") or {}).items():
            entry = phase_totals.setdefault(
                phase,
                {"count": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "seconds": 0.0},
            )
            entry["count"] += int(bucket.get("count", 0))
            entry["input_tokens"] += int(bucket.get("input_tokens", 0))
            entry["output_tokens"] += int(bucket.get("output_tokens", 0))
            entry["total_tokens"] += int(bucket.get("total_tokens", 0))
            entry["seconds"] += float(bucket.get("seconds", 0.0))

    final_block = None
    if final_cases:
        final_totals = {
            "input_tokens": sum(int(case.get("input_tokens", 0)) for case in final_cases),
            "output_tokens": sum(int(case.get("output_tokens", 0)) for case in final_cases),
            "total_tokens": sum(int(case.get("total_tokens", 0)) for case in final_cases),
            "num_generations": len(final_cases),
        }
        final_block = _finalize_block(final_totals, len(final_cases))

    estimated = None
    if input_price_per_1m > 0.0 or output_price_per_1m > 0.0:
        input_cost = totals["input_tokens"] * input_price_per_1m / 1_000_000
        output_cost = totals["output_tokens"] * output_price_per_1m / 1_000_000
        estimated = {
            "generation": {
                "input_cost_usd": input_cost,
                "output_cost_usd": output_cost,
                "total_cost_usd": input_cost + output_cost,
            }
        }

    return {
        "method": "tree_of_thoughts",
        "num_tasks": num_tasks,
        "branch_factor": branch_factor,
        "beam_width": beam_width,
        "depth": depth,
        "num_generations": totals["num_generations"],
        "generation": _finalize_block(totals, num_tasks),
        "per_task_avg_generation": _divide_block(totals, num_tasks),
        "by_phase": phase_totals,
        "final_answer": final_block,
        "estimated_cost_usd": estimated,
        "note": (
            "ToT counts every LLM call: thought proposals, optional value scoring, "
            "and code expansions under surviving beams."
        ),
    }


def build_per_task_tot_records(task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """导出逐题 ToT token / 候选规模记录。"""
    rows = []
    for record in task_records:
        stats = record.get("token_stats") or summarize_task_nodes(record.get("nodes", []))
        rows.append(
            {
                "task_id": int(record["task_id"]),
                "num_nodes": int(stats.get("num_generations", 0)),
                "num_thoughts": int(record.get("num_thoughts", 0)),
                "num_kept_thoughts": int(record.get("num_kept_thoughts", 0)),
                "num_code_candidates": int(record.get("num_code_candidates", 0)),
                "passed": bool(record.get("passed")),
                "generation": {
                    "input_tokens": int(stats.get("input_tokens", 0)),
                    "output_tokens": int(stats.get("output_tokens", 0)),
                    "total_tokens": int(stats.get("total_tokens", 0)),
                },
                "by_phase": stats.get("by_phase", {}),
            }
        )
    return rows


def summarize_tot_timing(
    *,
    num_tasks: int,
    branch_factor: int,
    beam_width: int,
    depth: int,
    total_seconds: float,
    model_load_seconds: float,
    thought_generation_seconds: float,
    value_generation_seconds: float,
    code_generation_seconds: float,
    scoring_seconds: float,
    selection_seconds: float,
    num_thought_generations: int,
    num_value_generations: int,
    num_code_generations: int,
    num_scored_candidates: int,
    skipped_generation: bool = False,
) -> dict[str, Any]:
    """汇总 ToT 各阶段（thought/value/code/scoring/selection）耗时。"""
    generation_seconds = (
        thought_generation_seconds + value_generation_seconds + code_generation_seconds
    )
    accounted = (
        model_load_seconds + generation_seconds + scoring_seconds + selection_seconds
    )
    return {
        "method": "tree_of_thoughts",
        "num_tasks": num_tasks,
        "branch_factor": branch_factor,
        "beam_width": beam_width,
        "depth": depth,
        "skipped_generation": skipped_generation,
        "total_seconds": round(total_seconds, 3),
        "accounted_seconds": round(accounted, 3),
        "unaccounted_seconds": round(max(0.0, total_seconds - accounted), 3),
        "model_load_seconds": round(model_load_seconds, 3),
        "generation_seconds": round(generation_seconds, 3),
        "scoring_seconds": round(scoring_seconds, 3),
        "selection_seconds": round(selection_seconds, 3),
        "avg_seconds_per_task": round(total_seconds / num_tasks, 4) if num_tasks else 0.0,
        "phases": {
            "thought": _phase_timing(thought_generation_seconds, num_thought_generations, num_tasks),
            "value": _phase_timing(value_generation_seconds, num_value_generations, num_tasks),
            "code": _phase_timing(code_generation_seconds, num_code_generations, num_tasks),
            "scoring": {
                "seconds": round(scoring_seconds, 3),
                "num_items": num_scored_candidates,
                "seconds_per_item": (
                    round(scoring_seconds / num_scored_candidates, 4)
                    if num_scored_candidates
                    else 0.0
                ),
            },
            "selection": {
                "seconds": round(selection_seconds, 3),
                "num_items": num_tasks,
                "seconds_per_item": round(selection_seconds / num_tasks, 4) if num_tasks else 0.0,
            },
        },
        "note": (
            "total_seconds is end-to-end wall time. generation_seconds sums thought, "
            "value, and code model.generate calls. scoring_seconds covers verifier/tests."
        ),
    }


def attach_token_stats_from_text(
    nodes: list[dict[str, Any]],
    tokenizer: Any,
    *,
    apply_chat_template_fn=None,
) -> None:
    """对缺少 token 字段的节点，用保存文本回填 input/output tokens。"""
    for item in nodes:
        if all(key in item for key in ("input_tokens", "output_tokens", "total_tokens")):
            continue
        stats = count_text_tokens(
            tokenizer,
            item.get("prompt", ""),
            item.get("completion", ""),
            apply_chat_template_fn=apply_chat_template_fn,
        )
        item.update(stats)


def _phase_timing(seconds: float, num_generations: int, num_tasks: int) -> dict[str, float]:
    """单阶段耗时派生指标（每 generate / 每题平均）。"""
    return {
        "seconds": round(seconds, 3),
        "num_generations": num_generations,
        "seconds_per_generation": round(seconds / num_generations, 4) if num_generations else 0.0,
        "seconds_per_task": round(seconds / num_tasks, 4) if num_tasks else 0.0,
    }


def _empty_block() -> dict[str, float]:
    """空的 token 汇总块占位。"""
    return {
        "num_generations": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "avg_input_tokens_per_task": 0.0,
        "avg_output_tokens_per_task": 0.0,
        "avg_total_tokens_per_task": 0.0,
    }


def _finalize_block(totals: dict[str, Any], num_tasks: int) -> dict[str, Any]:
    """把累计 totals 转成带 avg_*_per_task 的 token 块。"""
    return {
        "num_generations": int(totals.get("num_generations", 0)),
        "input_tokens": int(totals.get("input_tokens", 0)),
        "output_tokens": int(totals.get("output_tokens", 0)),
        "total_tokens": int(totals.get("total_tokens", 0)),
        "avg_input_tokens_per_task": totals["input_tokens"] / num_tasks if num_tasks else 0.0,
        "avg_output_tokens_per_task": totals["output_tokens"] / num_tasks if num_tasks else 0.0,
        "avg_total_tokens_per_task": totals["total_tokens"] / num_tasks if num_tasks else 0.0,
    }


def _divide_block(totals: dict[str, Any], divisor: int) -> dict[str, float]:
    """按题数（或除数）平均 token 块。"""
    if divisor <= 0:
        return _empty_block()
    return {
        "num_generations": totals.get("num_generations", 0) / divisor,
        "input_tokens": totals["input_tokens"] / divisor,
        "output_tokens": totals["output_tokens"] / divisor,
        "total_tokens": totals["total_tokens"] / divisor,
        "avg_input_tokens_per_task": totals["input_tokens"] / divisor,
        "avg_output_tokens_per_task": totals["output_tokens"] / divisor,
        "avg_total_tokens_per_task": totals["total_tokens"] / divisor,
    }
