"""ToT 候选代码打分：语法 / 格式 / 函数名 / 测试执行的 verifier。

输入 / 输出（函数契约）
------------------------
make_evaluator(test_timeout, memory_mb, weight_*, ...) -> CodeRewardEvaluator
    入：超时、内存、各分项权重；出：可对 completion 打分的 evaluator

build_task_meta(row, config, include_challenge, row_*_fn...) -> dict
    入：一条 MBPP 行 + 字段抽取函数
    出：{task_id, prompt, reference_code, tests, setup_code}

score_candidate(sample, meta, evaluator) -> dict
    入：候选 sample（含 completion/code）+ task meta + evaluator
    出：原 sample 叠加 syntax_ok / passed / verifier_score / test_pass_rate 等

依赖：rl.reward.code_reward.CodeRewardEvaluator（子进程执行 assert）。
由 mbpp_eval_tot.py 在 code 阶段调用；本文件无直接文件 I/O。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

A5_ROOT = Path(__file__).resolve().parent
ASSIGNMENT_ROOT = A5_ROOT.parent
if str(ASSIGNMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(ASSIGNMENT_ROOT))

from rl.reward.code_reward import CodeRewardConfig, CodeRewardEvaluator  # noqa: E402


def build_task_meta(
    row: dict[str, Any],
    config: str,
    include_challenge: bool,
    *,
    row_prompt_fn,
    row_setup_fn,
    row_tests_fn,
) -> dict[str, Any]:
    """从 MBPP 行构造 verifier 所需的 task meta（题目、参考代码、setup、tests）。"""
    reference_code = str(row.get("code", "") or "").strip()
    return {
        "task_id": int(row["task_id"]),
        "prompt": row_prompt_fn(row, config),
        "reference_code": reference_code,
        "tests": row_tests_fn(row, include_challenge),
        "setup_code": row_setup_fn(row, config),
    }


def score_candidate(
    sample: dict[str, Any],
    meta: dict[str, Any],
    evaluator: CodeRewardEvaluator,
) -> dict[str, Any]:
    """对单个代码候选调用 verifier，回填 passed / syntax / verifier_score 等字段。"""
    completion = sample.get("completion", "")
    breakdown = evaluator.score(completion, meta)
    return {
        **sample,
        "code": breakdown.code or sample.get("code", ""),
        "syntax_ok": breakdown.syntax_ok,
        "format_ok": breakdown.format_ok,
        "func_name_ok": breakdown.func_name_ok,
        "passed_tests": breakdown.passed_tests,
        "total_tests": breakdown.total_tests,
        "passed": breakdown.total_tests > 0 and breakdown.passed_tests == breakdown.total_tests,
        "test_pass_rate": breakdown.test_pass_rate,
        "verifier_score": breakdown.total,
        "verifier_components": breakdown.components,
        "expected_func_name": breakdown.expected_func_name,
        "extracted_func_names": breakdown.extracted_func_names,
    }


def make_evaluator(
    *,
    test_timeout: float,
    memory_mb: int,
    weight_format: float,
    weight_syntax: float,
    weight_func_name: float,
    weight_tests: float,
    require_fenced_or_begin: bool,
) -> CodeRewardEvaluator:
    """按权重与资源限制构造 CodeRewardEvaluator。"""
    return CodeRewardEvaluator(
        CodeRewardConfig(
            weight_format=weight_format,
            weight_syntax=weight_syntax,
            weight_func_name=weight_func_name,
            weight_tests=weight_tests,
            test_timeout=test_timeout,
            memory_mb=memory_mb,
            require_fenced_or_begin=require_fenced_or_begin,
        )
    )
