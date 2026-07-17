#!/usr/bin/env python3
"""Tree of Thoughts（ToT）MBPP 评测主入口。

流程（每题）
------------
1. 采样 branch_factor 条中间 thought（计划）
2. 对 thought 打分（llm / heuristic）并剪枝到 beam_width
3. 每个保留 thought 再扩展 branch_factor 条代码候选
4. 用 verifier（语法/格式/函数名/测试）打分并选最优路径

输入
----
- MBPP parquet：`--mbpp_dir/{config}/{split}-00000-of-00001.parquet`
- 模型目录：`--model_path`
- 可选 `--records_path` / 默认 `{output_dir}/mbpp_tot_records.jsonl`
  （仅 `--skip_generation` 时作为输入重读）

CLI 关键参数
------------
--branch_factor / --beam_width / --depth（当前仅支持 depth=2）
--value_mode heuristic|llm
--temperature / --top_p（thought/code 采样；非 greedy）
--max_new_tokens / --max_thought_tokens / --max_value_tokens
--weight_*（verifier 权重）
--limit / --batch_size / --test_timeout / --memory_mb
--input_price_per_1m / --output_price_per_1m

输出（默认 `a5_cgh/outputs/eval_tot/`）
---------------------------------------
- mbpp_tot_records.jsonl           每题完整搜索树：nodes, thoughts, code_candidates, selected
- mbpp_nodes_tot.jsonl             与 records 同结构的节点级落盘（当前实现写的是 task_records）
- mbpp_cases_tot.jsonl             最终选中代码的判题 case（含 selection / verifier）
- mbpp_metrics_tot.json            pass@1_tot, oracle, token_cost, timing
- token_cost.json / timing.json
- mbpp_token_cost_per_task.jsonl   逐题 token 与候选规模
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from candidate_scoring import build_task_meta, make_evaluator, score_candidate
from tree_of_thoughts import (
    attach_token_stats_from_text,
    batch_generate,
    build_code_prompt,
    build_per_task_tot_records,
    build_thought_prompt,
    build_value_prompt,
    heuristic_thought_score,
    make_node_record,
    parse_value_score,
    prune_thoughts,
    select_best_code,
    summarize_task_nodes,
    summarize_tot_timing,
    summarize_tot_token_cost,
)

A5_ROOT = Path(__file__).resolve().parent
ASSIGNMENT_ROOT = A5_ROOT.parent
sys.path.insert(0, str(ASSIGNMENT_ROOT / "dpo" / "scripts"))

from mbpp_eval_dpo import (  # noqa: E402
    DEFAULT_MBPP_DIR,
    apply_chat_template,
    build_prompt,
    build_prompt_prefix,
    extract_candidate_code,
    load_model,
    load_split,
    read_jsonl,
    row_prompt,
    row_setup,
    row_tests,
    save_json,
    save_jsonl,
)
from eval_common import load_tokenizer, resolve_model_path  # noqa: E402


DEFAULT_MODEL_PATH = ASSIGNMENT_ROOT / "sft" / "outputs" / "qwen15_code_full_sft"
DEFAULT_OUTPUT_DIR = A5_ROOT / "outputs" / "eval_tot"


def parse_args() -> argparse.Namespace:
    """解析 ToT 评测 CLI 参数（beam / branch / value_mode 等）。"""
    parser = argparse.ArgumentParser(description="MBPP Tree-of-Thoughts evaluation")
    parser.add_argument("--mbpp_dir", type=Path, default=DEFAULT_MBPP_DIR)
    parser.add_argument("--model_path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config", choices=("sanitized", "full"), default="sanitized")
    parser.add_argument("--split", default="test")
    parser.add_argument(
        "--prompt_mode",
        choices=("zero_shot", "one_shot", "three_shot"),
        default="zero_shot",
    )
    parser.add_argument("--prompt_task_ids", default="2,3,4")
    parser.add_argument("--limit", type=int, default=0, help="0 means evaluate all rows.")
    parser.add_argument("--start_index", type=int, default=0)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--max_thought_tokens", type=int, default=256)
    parser.add_argument("--max_value_tokens", type=int, default=32)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--test_timeout", type=float, default=5.0)
    parser.add_argument("--memory_mb", type=int, default=1024)
    parser.add_argument("--include_challenge_tests", action="store_true")
    parser.add_argument("--trust_remote_code", action="store_true", default=True)
    parser.add_argument(
        "--branch_factor",
        type=int,
        default=3,
        help="Number of children expanded from each kept node.",
    )
    parser.add_argument(
        "--beam_width",
        type=int,
        default=2,
        help="Number of thoughts kept after pruning.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Search depth (2 = thought then code). Currently fixed to 2 levels.",
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument(
        "--value_mode",
        choices=("llm", "heuristic"),
        default="heuristic",
        help="How to score intermediate thoughts before pruning.",
    )
    parser.add_argument("--weight_format", type=float, default=0.10)
    parser.add_argument("--weight_syntax", type=float, default=0.15)
    parser.add_argument("--weight_func_name", type=float, default=0.15)
    parser.add_argument("--weight_tests", type=float, default=0.60)
    parser.add_argument(
        "--require_fenced_or_begin",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--skip_generation", action="store_true")
    parser.add_argument("--records_path", type=Path, default=None)
    parser.add_argument("--input_price_per_1m", type=float, default=0.0)
    parser.add_argument("--output_price_per_1m", type=float, default=0.0)
    return parser.parse_args()


def _batched(items: list[Any], batch_size: int):
    """按 batch_size 切分列表的生成器。"""
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def run_tot_search(
    eval_rows: list[dict[str, Any]],
    prompts: list[str],
    model_path: Path,
    args: argparse.Namespace,
    evaluator,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """对每题跑 thought→prune→code→score→select，返回 task_records 与阶段 timing。"""
    load_start = time.perf_counter()
    tokenizer, model, torch = load_model(model_path, args.trust_remote_code)
    model_load_seconds = time.perf_counter() - load_start

    timing = {
        "model_load_seconds": model_load_seconds,
        "thought_generation_seconds": 0.0,
        "value_generation_seconds": 0.0,
        "code_generation_seconds": 0.0,
        "scoring_seconds": 0.0,
        "selection_seconds": 0.0,
        "num_thought_generations": 0,
        "num_value_generations": 0,
        "num_code_generations": 0,
        "num_scored_candidates": 0,
    }

    task_states: dict[int, dict[str, Any]] = {}
    for row, prompt in zip(eval_rows, prompts):
        task_id = int(row["task_id"])
        task_states[task_id] = {
            "task_id": task_id,
            "prompt": row_prompt(row, args.config),
            "original_prompt": prompt,
            "reference_code": row.get("code", ""),
            "row": row,
            "nodes": [],
            "thoughts": [],
            "kept_thoughts": [],
            "code_candidates": [],
        }

    task_ids = list(task_states.keys())

    # --- Depth 1: propose thoughts ---
    thought_jobs: list[tuple[int, int, str]] = []
    for task_id in task_ids:
        thought_prompt = build_thought_prompt(
            original_prompt=task_states[task_id]["original_prompt"]
        )
        for branch_index in range(args.branch_factor):
            thought_jobs.append((task_id, branch_index, thought_prompt))

    for batch in _batched(thought_jobs, args.batch_size):
        batch_prompts = [item[2] for item in batch]
        completions, token_stats_list, elapsed = batch_generate(
            batch_prompts,
            tokenizer=tokenizer,
            model=model,
            torch=torch,
            max_new_tokens=args.max_thought_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            greedy=False,
            apply_chat_template_fn=apply_chat_template,
        )
        timing["thought_generation_seconds"] += elapsed
        timing["num_thought_generations"] += len(batch)

        for (task_id, branch_index, thought_prompt), completion, token_stats in zip(
            batch, completions, token_stats_list
        ):
            thought_text = completion.strip()
            node_id = f"{task_id}:t{branch_index}"
            node = make_node_record(
                task_id=task_id,
                node_id=node_id,
                depth=1,
                phase="thought",
                parent_id=None,
                prompt=thought_prompt,
                completion=completion,
                thought=thought_text,
                token_stats=token_stats,
                elapsed_seconds=elapsed / max(len(batch), 1),
                extra={"branch_index": branch_index},
            )
            task_states[task_id]["nodes"].append(node)
            task_states[task_id]["thoughts"].append(node)

    # --- Score / prune thoughts ---
    if args.value_mode == "llm":
        value_jobs: list[tuple[int, dict[str, Any], str]] = []
        for task_id in task_ids:
            state = task_states[task_id]
            for thought_node in state["thoughts"]:
                value_prompt = build_value_prompt(
                    task_prompt=state["prompt"],
                    thought=thought_node["thought"],
                )
                value_jobs.append((task_id, thought_node, value_prompt))

        for batch in _batched(value_jobs, args.batch_size):
            batch_prompts = [item[2] for item in batch]
            completions, token_stats_list, elapsed = batch_generate(
                batch_prompts,
                tokenizer=tokenizer,
                model=model,
                torch=torch,
                max_new_tokens=args.max_value_tokens,
                temperature=0.0,
                top_p=1.0,
                greedy=True,
                apply_chat_template_fn=apply_chat_template,
            )
            timing["value_generation_seconds"] += elapsed
            timing["num_value_generations"] += len(batch)

            for (task_id, thought_node, value_prompt), completion, token_stats in zip(
                batch, completions, token_stats_list
            ):
                score = parse_value_score(completion)
                thought_node["value_score"] = score
                value_node = make_node_record(
                    task_id=task_id,
                    node_id=f"{thought_node['node_id']}:v",
                    depth=1,
                    phase="value",
                    parent_id=thought_node["node_id"],
                    prompt=value_prompt,
                    completion=completion,
                    thought=thought_node["thought"],
                    value_score=score,
                    token_stats=token_stats,
                    elapsed_seconds=elapsed / max(len(batch), 1),
                )
                task_states[task_id]["nodes"].append(value_node)
    else:
        for task_id in task_ids:
            for thought_node in task_states[task_id]["thoughts"]:
                thought_node["value_score"] = heuristic_thought_score(thought_node["thought"])

    for task_id in task_ids:
        kept = prune_thoughts(task_states[task_id]["thoughts"], args.beam_width)
        task_states[task_id]["kept_thoughts"] = kept

    # --- Depth 2: expand code under kept thoughts ---
    code_jobs: list[tuple[int, dict[str, Any], int, str]] = []
    for task_id in task_ids:
        state = task_states[task_id]
        for thought_node in state["kept_thoughts"]:
            code_prompt = build_code_prompt(
                original_prompt=state["original_prompt"],
                thought=thought_node["thought"],
            )
            for branch_index in range(args.branch_factor):
                code_jobs.append((task_id, thought_node, branch_index, code_prompt))

    for batch in _batched(code_jobs, args.batch_size):
        batch_prompts = [item[3] for item in batch]
        completions, token_stats_list, elapsed = batch_generate(
            batch_prompts,
            tokenizer=tokenizer,
            model=model,
            torch=torch,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            greedy=False,
            apply_chat_template_fn=apply_chat_template,
        )
        timing["code_generation_seconds"] += elapsed
        timing["num_code_generations"] += len(batch)

        for (task_id, thought_node, branch_index, code_prompt), completion, token_stats in zip(
            batch, completions, token_stats_list
        ):
            code = extract_candidate_code(completion)
            node_id = f"{thought_node['node_id']}:c{branch_index}"
            node = make_node_record(
                task_id=task_id,
                node_id=node_id,
                depth=2,
                phase="code",
                parent_id=thought_node["node_id"],
                prompt=code_prompt,
                completion=completion,
                thought=thought_node["thought"],
                code=code,
                value_score=thought_node.get("value_score"),
                token_stats=token_stats,
                elapsed_seconds=elapsed / max(len(batch), 1),
                extra={
                    "branch_index": branch_index,
                    "parent_value_score": thought_node.get("value_score"),
                    "sample_id": len(task_states[task_id]["code_candidates"]),
                },
            )
            task_states[task_id]["nodes"].append(node)
            task_states[task_id]["code_candidates"].append(node)

    # --- Score code candidates and select best ---
    task_records: list[dict[str, Any]] = []
    for row in eval_rows:
        task_id = int(row["task_id"])
        state = task_states[task_id]
        meta = build_task_meta(
            row,
            args.config,
            args.include_challenge_tests,
            row_prompt_fn=row_prompt,
            row_setup_fn=row_setup,
            row_tests_fn=row_tests,
        )

        scored: list[dict[str, Any]] = []
        score_start = time.perf_counter()
        for candidate in state["code_candidates"]:
            sample = {
                "task_id": task_id,
                "sample_id": candidate.get("sample_id", 0),
                "completion": candidate.get("completion", ""),
                "code": candidate.get("code", ""),
                "input_tokens": candidate.get("input_tokens", 0),
                "output_tokens": candidate.get("output_tokens", 0),
                "total_tokens": candidate.get("total_tokens", 0),
                "node_id": candidate.get("node_id"),
                "parent_id": candidate.get("parent_id"),
                "branch_index": candidate.get("branch_index", 0),
                "parent_value_score": candidate.get("parent_value_score"),
                "thought": candidate.get("thought", ""),
            }
            scored_sample = score_candidate(sample, meta, evaluator)
            scored_sample["node_id"] = candidate.get("node_id")
            scored_sample["parent_id"] = candidate.get("parent_id")
            scored_sample["parent_value_score"] = candidate.get("parent_value_score")
            scored_sample["thought"] = candidate.get("thought", "")
            scored_sample["branch_index"] = candidate.get("branch_index", 0)
            scored.append(scored_sample)
        timing["scoring_seconds"] += time.perf_counter() - score_start
        timing["num_scored_candidates"] += len(scored)

        select_start = time.perf_counter()
        selected, selection_meta = select_best_code(scored)
        timing["selection_seconds"] += time.perf_counter() - select_start

        token_stats = summarize_task_nodes(state["nodes"])
        task_records.append(
            {
                "task_id": task_id,
                "prompt": state["prompt"],
                "reference_code": state.get("reference_code", ""),
                "num_thoughts": len(state["thoughts"]),
                "num_kept_thoughts": len(state["kept_thoughts"]),
                "num_code_candidates": len(scored),
                "passed": bool(selected.get("passed")),
                "nodes": state["nodes"],
                "kept_thought_ids": [item["node_id"] for item in state["kept_thoughts"]],
                "code_candidates": scored,
                "selected": selected,
                "selection": selection_meta,
                "token_stats": token_stats,
            }
        )

    return task_records, timing


def build_final_cases(task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从每题 selected 候选展开为与 baseline 对齐的最终 cases 列表。"""
    cases = []
    for record in task_records:
        selected = record.get("selected") or {}
        cases.append(
            {
                **selected,
                "task_id": record["task_id"],
                "selection": record.get("selection", {}),
                "num_thoughts": record.get("num_thoughts", 0),
                "num_kept_thoughts": record.get("num_kept_thoughts", 0),
                "num_code_candidates": record.get("num_code_candidates", 0),
            }
        )
    return cases


def build_metrics(
    *,
    args: argparse.Namespace,
    task_records: list[dict[str, Any]],
    final_cases: list[dict[str, Any]],
    loop_timing: dict[str, Any],
    total_seconds: float,
    records_path: Path,
) -> dict[str, Any]:
    """汇总 ToT 的 pass@1 / oracle / token_cost / timing 等指标。"""
    total = len(final_cases)
    passed = sum(1 for case in final_cases if case.get("passed"))
    syntax_ok = sum(1 for case in final_cases if case.get("syntax_ok"))
    total_tests = sum(case.get("total_tests", 0) for case in final_cases)
    passed_tests = sum(case.get("passed_tests", 0) for case in final_cases)
    oracle_passed = sum(
        1
        for record in task_records
        if any(item.get("passed") for item in record.get("code_candidates", []))
    )

    timing = summarize_tot_timing(
        num_tasks=total,
        branch_factor=args.branch_factor,
        beam_width=args.beam_width,
        depth=args.depth,
        total_seconds=total_seconds,
        model_load_seconds=loop_timing.get("model_load_seconds", 0.0),
        thought_generation_seconds=loop_timing.get("thought_generation_seconds", 0.0),
        value_generation_seconds=loop_timing.get("value_generation_seconds", 0.0),
        code_generation_seconds=loop_timing.get("code_generation_seconds", 0.0),
        scoring_seconds=loop_timing.get("scoring_seconds", 0.0),
        selection_seconds=loop_timing.get("selection_seconds", 0.0),
        num_thought_generations=loop_timing.get("num_thought_generations", 0),
        num_value_generations=loop_timing.get("num_value_generations", 0),
        num_code_generations=loop_timing.get("num_code_generations", 0),
        num_scored_candidates=loop_timing.get("num_scored_candidates", 0),
        skipped_generation=args.skip_generation,
    )

    return {
        "benchmark": "MBPP",
        "method": "tree_of_thoughts",
        "config": args.config,
        "split": args.split,
        "model_path": str(resolve_model_path(args.model_path)),
        "records_path": str(records_path),
        "num_tasks": total,
        "branch_factor": args.branch_factor,
        "beam_width": args.beam_width,
        "depth": args.depth,
        "value_mode": args.value_mode,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "pass_at_1_tot": passed / total if total else 0.0,
        "pass_at_n_oracle": oracle_passed / total if total else 0.0,
        "syntax_pass_rate_tot": syntax_ok / total if total else 0.0,
        "avg_test_pass_rate_tot": passed_tests / total_tests if total_tests else 0.0,
        "passed_tasks_tot": passed,
        "passed_tasks_oracle": oracle_passed,
        "oracle_gap": (oracle_passed - passed) / total if total else 0.0,
        "total_tests": total_tests,
        "passed_tests_tot": passed_tests,
        "avg_code_candidates": (
            sum(int(record.get("num_code_candidates", 0)) for record in task_records) / total
            if total
            else 0.0
        ),
        "prompt": {
            "mode": args.prompt_mode,
            "example_task_ids": [
                int(item) for item in args.prompt_task_ids.split(",") if item.strip()
            ],
        },
        "execution_note": (
            "Tree of Thoughts proposes multiple intermediate plans, scores/prunes them "
            "to a beam, expands each surviving plan into code candidates, then selects "
            "the highest-scoring executable solution."
        ),
        "token_cost": summarize_tot_token_cost(
            task_records,
            final_cases=final_cases,
            branch_factor=args.branch_factor,
            beam_width=args.beam_width,
            depth=args.depth,
            input_price_per_1m=args.input_price_per_1m,
            output_price_per_1m=args.output_price_per_1m,
        ),
        "timing": timing,
    }


def main() -> None:
    """ToT 评测入口：加载 → 搜索或 skip_generation → 写 metrics/cases/token/timing。"""
    args = parse_args()
    if args.depth != 2:
        raise ValueError("Current ToT implementation supports depth=2 only (thought -> code).")
    if args.branch_factor < 1:
        raise ValueError("--branch_factor must be >= 1")
    if args.beam_width < 1:
        raise ValueError("--beam_width must be >= 1")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = resolve_model_path(args.model_path)
    records_path = args.records_path or (args.output_dir / "mbpp_tot_records.jsonl")

    evaluator = make_evaluator(
        test_timeout=args.test_timeout,
        memory_mb=args.memory_mb,
        weight_format=args.weight_format,
        weight_syntax=args.weight_syntax,
        weight_func_name=args.weight_func_name,
        weight_tests=args.weight_tests,
        require_fenced_or_begin=args.require_fenced_or_begin,
    )

    prompt_ids = [int(item) for item in args.prompt_task_ids.split(",") if item.strip()]
    prompt_rows = load_split(args.mbpp_dir, args.config, "prompt")
    eval_rows = load_split(args.mbpp_dir, args.config, args.split)
    eval_rows = eval_rows[args.start_index :]
    if args.limit > 0:
        eval_rows = eval_rows[: args.limit]

    prefix = build_prompt_prefix(prompt_rows, args.config, args.prompt_mode, prompt_ids)
    prompts = [
        build_prompt(prefix, row, args.config, args.include_challenge_tests)
        for row in eval_rows
    ]

    total_start = time.perf_counter()
    loop_timing: dict[str, Any] = {}

    if args.skip_generation:
        task_records = read_jsonl(records_path)
        tokenizer = load_tokenizer(model_path, args.trust_remote_code)
        for record in task_records:
            attach_token_stats_from_text(
                record.get("nodes", []),
                tokenizer,
                apply_chat_template_fn=apply_chat_template,
            )
            record["token_stats"] = summarize_task_nodes(record.get("nodes", []))
    else:
        task_records, loop_timing = run_tot_search(
            eval_rows,
            prompts,
            model_path,
            args,
            evaluator,
        )
        save_jsonl(records_path, task_records)

    final_cases = build_final_cases(task_records)
    save_jsonl(args.output_dir / "mbpp_cases_tot.jsonl", final_cases)
    save_jsonl(args.output_dir / "mbpp_nodes_tot.jsonl", task_records)

    total_seconds = time.perf_counter() - total_start
    metrics = build_metrics(
        args=args,
        task_records=task_records,
        final_cases=final_cases,
        loop_timing=loop_timing,
        total_seconds=total_seconds,
        records_path=records_path,
    )
    save_json(args.output_dir / "mbpp_metrics_tot.json", metrics)
    save_json(args.output_dir / "token_cost.json", metrics["token_cost"])
    save_json(args.output_dir / "timing.json", metrics["timing"])
    save_jsonl(
        args.output_dir / "mbpp_token_cost_per_task.jsonl",
        build_per_task_tot_records(task_records),
    )

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Wrote records to {records_path}")
    print(f"Wrote metrics to {args.output_dir / 'mbpp_metrics_tot.json'}")
    print(f"Wrote token cost to {args.output_dir / 'token_cost.json'}")
    print(f"Wrote timing to {args.output_dir / 'timing.json'}")
    _print_cost_summary(metrics)


def _print_cost_summary(metrics: dict[str, Any]) -> None:
    """向 stdout 打印简短 token / timing 摘要。"""
    token_cost = metrics.get("token_cost", {})
    timing = metrics.get("timing", {})
    generation = token_cost.get("generation", {})
    print(
        "Token cost summary: "
        f"total={generation.get('total_tokens', 0)} "
        f"(in={generation.get('input_tokens', 0)}, out={generation.get('output_tokens', 0)}); "
        f"generations={generation.get('num_generations', 0)}"
    )
    by_phase = token_cost.get("by_phase") or {}
    if by_phase:
        parts = [
            f"{phase}={bucket.get('total_tokens', 0)}"
            for phase, bucket in sorted(by_phase.items())
        ]
        print("Tokens by phase: " + ", ".join(parts))
    print(
        "Timing summary: "
        f"total={timing.get('total_seconds', 0)}s, "
        f"generation={timing.get('generation_seconds', 0)}s, "
        f"scoring={timing.get('scoring_seconds', 0)}s, "
        f"avg_per_task={timing.get('avg_seconds_per_task', 0)}s"
    )


if __name__ == "__main__":
    main()
