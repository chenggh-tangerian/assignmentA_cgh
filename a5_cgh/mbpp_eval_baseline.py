#!/usr/bin/env python3
"""Greedy / CoT 单路径 MBPP 评测主入口（--method greedy|cot）。

输入
----
- MBPP parquet：`--mbpp_dir/{sanitized|full}/{split}-00000-of-00001.parquet`
  默认 `--mbpp_dir` 指向仓库外的 `mbpp/`（由 dpo/scripts/mbpp_eval_dpo.DEFAULT_MBPP_DIR 提供）
- 模型目录：`--model_path`（支持完整权重或 LoRA adapter）
- 可选 `--records_path` / 默认 `{output_dir}/mbpp_{method}_records.jsonl`
  （仅 `--skip_generation` 时作为输入重读，不再跑模型）

CLI 关键参数
------------
--method greedy|cot
--config sanitized|full   --split test（等）
--prompt_mode zero_shot|one_shot|three_shot   （主要影响 greedy）
--cot_include_examples    （仅 cot：拼接 few-shot CoT 示例）
--limit / --batch_size / --max_new_tokens
--test_timeout / --memory_mb
--input_price_per_1m / --output_price_per_1m

输出（`--output_dir`，默认 eval_greedy 或 eval_cot）
----------------------------------------------------
- mbpp_{method}_records.jsonl      原始生成：task_id, prompt, completion, code, tokens
- mbpp_cases_{method}.jsonl        判题结果：passed, syntax_ok, test_results, tokens
- mbpp_metrics_{method}.json       汇总：pass@1, syntax, token_cost, timing
- token_cost.json                  从 metrics 抽出的 token 成本
- timing.json                      从 metrics 抽出的耗时
- mbpp_token_cost_per_task_{method}.jsonl  逐题 token

策略差异（同一入口）
--------------------
- greedy：MBPP 官方 [BEGIN]/[DONE] + extract_candidate_code，max_new_tokens 默认 512
- cot：cot_code_example 结构化 Prompt + extract_final_code，max_new_tokens 默认 768
- 解码均为 temperature=0（do_sample=False）单路径一次 generate
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from baseline_common import (
    build_per_task_token_records,
    generate_single_path_completions,
    summarize_single_path_timing,
    summarize_single_path_token_cost,
)
from cot_code_example import build_chat_messages, extract_final_code


A5_ROOT = Path(__file__).resolve().parent
ASSIGNMENT_ROOT = A5_ROOT.parent
sys.path.insert(0, str(ASSIGNMENT_ROOT / "dpo" / "scripts"))

from mbpp_eval_dpo import (  # noqa: E402
    DEFAULT_MBPP_DIR,
    OFFICIAL_PROMPT_TEMPLATE,
    apply_chat_template,
    build_prompt,
    build_prompt_prefix,
    evaluate_generation,
    extract_candidate_code,
    load_model,
    load_split,
    read_jsonl,
    row_prompt,
    row_tests,
    save_json,
    save_jsonl,
)
from eval_common import resolve_model_path  # noqa: E402


DEFAULT_MODEL_PATH = ASSIGNMENT_ROOT / "rl" / "outputs" / "train_lora_ppo_full" / "checkpoint-1304"
DEFAULT_OUTPUT_GREEDY = A5_ROOT / "outputs" / "eval_greedy"
DEFAULT_OUTPUT_COT = A5_ROOT / "outputs" / "eval_cot"


def parse_args() -> argparse.Namespace:
    """解析 Greedy/CoT 评测 CLI 参数。"""
    parser = argparse.ArgumentParser(description="MBPP greedy / CoT baseline evaluation")
    parser.add_argument(
        "--method",
        choices=("greedy", "cot"),
        required=True,
        help="greedy: MBPP official prompt; cot: Chain-of-Thought structured prompt.",
    )
    parser.add_argument("--mbpp_dir", type=Path, default=DEFAULT_MBPP_DIR)
    parser.add_argument("--model_path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output_dir", type=Path, default=None)
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
    parser.add_argument("--max_new_tokens", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--test_timeout", type=float, default=5.0)
    parser.add_argument("--memory_mb", type=int, default=1024)
    parser.add_argument("--include_challenge_tests", action="store_true")
    parser.add_argument("--trust_remote_code", action="store_true", default=True)
    parser.add_argument(
        "--cot_include_examples",
        action="store_true",
        help="Include few-shot CoT examples in the prompt (cot method only).",
    )
    parser.add_argument("--skip_generation", action="store_true")
    parser.add_argument("--records_path", type=Path, default=None)
    parser.add_argument("--input_price_per_1m", type=float, default=0.0)
    parser.add_argument("--output_price_per_1m", type=float, default=0.0)
    return parser.parse_args()


def build_cot_task_text(row: dict[str, Any], config: str, include_challenge: bool) -> str:
    """把 MBPP 题目 + assert 拼成 CoT 的 task_description（不含 [BEGIN]/[DONE]）。"""
    prompt = row_prompt(row, config)
    tests = row_tests(row, include_challenge)
    if tests:
        return f"{prompt}\n\nYour code should pass these tests:\n" + "\n".join(tests)
    return prompt


def apply_cot_chat_template(tokenizer: Any, task_text: str, include_examples: bool) -> str:
    """用 CoT chat messages 渲染最终模型输入。"""
    messages = build_chat_messages(task_text, include_examples=include_examples)
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    system = messages[0]["content"]
    user = messages[1]["content"]
    return f"{system}\n\nUser:\n{user}\n\nAssistant:\n"


def build_rendered_prompts(
    args: argparse.Namespace,
    eval_rows: list[dict[str, Any]],
    prefix: str,
    tokenizer: Any | None = None,
) -> list[str]:
    """按 method 分叉：greedy 用官方 MBPP 模板；cot 用结构化 CoT prompt。"""
    if args.method == "greedy":
        prompts = [
            build_prompt(prefix, row, args.config, args.include_challenge_tests)
            for row in eval_rows
        ]
        return [apply_chat_template(tokenizer, prompt) if tokenizer else prompt for prompt in prompts]

    task_texts = [
        build_cot_task_text(row, args.config, args.include_challenge_tests)
        for row in eval_rows
    ]
    if tokenizer is None:
        return task_texts
    return [
        apply_cot_chat_template(tokenizer, task_text, args.cot_include_examples)
        for task_text in task_texts
    ]


def default_output_dir(method: str) -> Path:
    """返回该方法默认输出目录。"""
    return DEFAULT_OUTPUT_GREEDY if method == "greedy" else DEFAULT_OUTPUT_COT


def default_max_new_tokens(method: str) -> int:
    """Greedy=512；CoT=768（需容纳 Reasoning/Key steps）。"""
    return 512 if method == "greedy" else 768


def method_label(method: str) -> str:
    """写入 metrics 的方法名标签。"""
    return "greedy" if method == "greedy" else "chain_of_thought"


def execution_note(method: str) -> str:
    """生成 metrics 里的 execution_note 说明文字。"""
    if method == "greedy":
        return (
            "Greedy baseline uses the MBPP official prompt template with "
            "temperature=0 (do_sample=False) single-path decode."
        )
    return (
        "CoT baseline uses a structured Reasoning / Key steps / Final code prompt "
        "with temperature=0 greedy decode; only the Final code block is evaluated."
    )


def build_metrics(
    *,
    args: argparse.Namespace,
    cases: list[dict[str, Any]],
    records_path: Path,
    timing: dict[str, Any],
    total_seconds: float,
) -> dict[str, Any]:
    """汇总 pass@1 / syntax / token_cost / timing 等指标字典。"""
    total = len(cases)
    passed = sum(1 for case in cases if case.get("passed"))
    syntax_ok = sum(1 for case in cases if case.get("syntax_ok"))
    total_tests = sum(case.get("total_tests", 0) for case in cases)
    passed_tests = sum(case.get("passed_tests", 0) for case in cases)

    method = args.method
    pass_key = "pass_at_1_greedy" if method == "greedy" else "pass_at_1_cot"
    syntax_key = "syntax_pass_rate_greedy" if method == "greedy" else "syntax_pass_rate_cot"
    avg_key = "avg_test_pass_rate_greedy" if method == "greedy" else "avg_test_pass_rate_cot"
    passed_key = "passed_tasks_greedy" if method == "greedy" else "passed_tasks_cot"
    tests_key = "passed_tests_greedy" if method == "greedy" else "passed_tests_cot"

    prompt_info: dict[str, Any]
    if method == "greedy":
        prompt_info = {
            "source": "Google Research MBPP README",
            "template": OFFICIAL_PROMPT_TEMPLATE,
            "mode": args.prompt_mode,
            "example_task_ids": [
                int(item) for item in args.prompt_task_ids.split(",") if item.strip()
            ],
        }
    else:
        prompt_info = {
            "style": "CoT with Reasoning, Key steps, and Final code sections",
            "include_examples": args.cot_include_examples,
            "decode": "greedy (temperature=0)",
        }

    return {
        "benchmark": "MBPP",
        "method": method_label(method),
        "config": args.config,
        "split": args.split,
        "model_path": str(resolve_model_path(args.model_path)),
        "records_path": str(records_path),
        "num_tasks": total,
        pass_key: passed / total if total else 0.0,
        "pass_at_1": passed / total if total else 0.0,
        syntax_key: syntax_ok / total if total else 0.0,
        "syntax_pass_rate": syntax_ok / total if total else 0.0,
        avg_key: passed_tests / total_tests if total_tests else 0.0,
        "avg_test_pass_rate": passed_tests / total_tests if total_tests else 0.0,
        passed_key: passed,
        "passed_tasks": passed,
        "total_tests": total_tests,
        tests_key: passed_tests,
        "passed_tests": passed_tests,
        "max_new_tokens": args.max_new_tokens,
        "prompt": prompt_info,
        "execution_note": execution_note(method),
        "token_cost": summarize_single_path_token_cost(
            cases,
            method=method_label(method),
            input_price_per_1m=args.input_price_per_1m,
            output_price_per_1m=args.output_price_per_1m,
        ),
        "timing": timing,
        "total_seconds": round(total_seconds, 3),
    }


def main() -> None:
    """Greedy/CoT 评测入口：加载数据 → 生成 → assert 判题 → 写 metrics。"""
    args = parse_args()
    if args.output_dir is None:
        args.output_dir = default_output_dir(args.method)
    if args.max_new_tokens is None:
        args.max_new_tokens = default_max_new_tokens(args.method)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = resolve_model_path(args.model_path)
    records_path = args.records_path or (
        args.output_dir / f"mbpp_{args.method}_records.jsonl"
    )

    prompt_ids = [int(item) for item in args.prompt_task_ids.split(",") if item.strip()]
    prompt_rows = load_split(args.mbpp_dir, args.config, "prompt")
    eval_rows = load_split(args.mbpp_dir, args.config, args.split)
    eval_rows = eval_rows[args.start_index :]
    if args.limit > 0:
        eval_rows = eval_rows[: args.limit]

    prefix = build_prompt_prefix(prompt_rows, args.config, args.prompt_mode, prompt_ids)

    total_start = time.perf_counter()
    model_load_seconds = 0.0
    generation_seconds = 0.0
    num_generations = 0
    scoring_seconds = 0.0

    extract_code_fn = extract_candidate_code if args.method == "greedy" else extract_final_code

    if args.skip_generation:
        generations = read_jsonl(records_path)
    else:
        import gc

        gc.collect()
        load_start = time.perf_counter()
        tokenizer, model, torch = load_model(model_path, args.trust_remote_code)
        model_load_seconds = time.perf_counter() - load_start
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        rendered_prompts = build_rendered_prompts(args, eval_rows, prefix, tokenizer)

        generations, gen_timing = generate_single_path_completions(
            eval_rows,
            rendered_prompts,
            tokenizer=tokenizer,
            model=model,
            torch=torch,
            batch_size=args.batch_size,
            max_new_tokens=args.max_new_tokens,
            extract_code_fn=extract_code_fn,
            row_prompt_fn=lambda row: row_prompt(row, args.config),
            model_load_seconds=model_load_seconds,
        )
        generation_seconds = gen_timing["generation_seconds"]
        num_generations = int(gen_timing["num_generations"])
        save_jsonl(records_path, generations)

        del model
        del tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    scoring_start = time.perf_counter()
    cases = []
    for generation in generations:
        row = next(item for item in eval_rows if int(item["task_id"]) == int(generation["task_id"]))
        case = evaluate_generation(
            generation,
            row,
            args.config,
            args.include_challenge_tests,
            args.test_timeout,
            args.memory_mb,
        )
        case["input_tokens"] = generation.get("input_tokens", 0)
        case["output_tokens"] = generation.get("output_tokens", 0)
        case["total_tokens"] = generation.get("total_tokens", 0)
        cases.append(case)
    scoring_seconds = time.perf_counter() - scoring_start

    total_seconds = time.perf_counter() - total_start
    timing = summarize_single_path_timing(
        method=method_label(args.method),
        num_tasks=len(cases),
        total_seconds=total_seconds,
        model_load_seconds=model_load_seconds,
        generation_seconds=generation_seconds,
        num_generations=num_generations or len(cases),
        scoring_seconds=scoring_seconds,
        skipped_generation=args.skip_generation,
    )

    metrics = build_metrics(
        args=args,
        cases=cases,
        records_path=records_path,
        timing=timing,
        total_seconds=total_seconds,
    )

    metrics_filename = f"mbpp_metrics_{args.method}.json"
    save_json(args.output_dir / metrics_filename, metrics)
    save_jsonl(args.output_dir / f"mbpp_cases_{args.method}.jsonl", cases)
    save_json(args.output_dir / "token_cost.json", metrics["token_cost"])
    save_json(args.output_dir / "timing.json", metrics["timing"])
    save_jsonl(
        args.output_dir / f"mbpp_token_cost_per_task_{args.method}.jsonl",
        build_per_task_token_records(cases),
    )

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Wrote records to {records_path}")
    print(f"Wrote metrics to {args.output_dir / metrics_filename}")
    print(f"Wrote cases to {args.output_dir / f'mbpp_cases_{args.method}.jsonl'}")
    print(f"Wrote token cost to {args.output_dir / 'token_cost.json'}")
    print(f"Wrote timing to {args.output_dir / 'timing.json'}")


if __name__ == "__main__":
    main()
