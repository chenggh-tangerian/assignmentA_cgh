#!/usr/bin/env python3
"""
功能: 对 MBPP 评测 cases 做事后错误分类与改进建议报告。

输入:  --cases mbpp_cases.jsonl, 可选 --metrics mbpp_metrics.json
输出:  error_analysis.md / error_report.json / error_cases_enriched.jsonl 等
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PROJECT_ROOT / "sft" / "outputs" / "eval_mbpp" / "mbpp_cases.jsonl"
DEFAULT_METRICS = PROJECT_ROOT / "sft" / "outputs" / "eval_mbpp" / "mbpp_metrics.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "sft" / "outputs_cgh"

ASSERT_FUNC_RE = re.compile(r"assert\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(")
DEF_FUNC_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", re.MULTILINE)

ERROR_CATEGORIES = [
    "pass_all",
    "syntax_error",
    "truncation_or_repetition",
    "function_name_mismatch",
    "import_error",
    "type_error",
    "boundary_error",
    "assertion_failure",
    "attribute_error",
    "timeout",
    "partial_pass",
    "other_runtime",
    "no_tests",
]

CATEGORY_LABELS_ZH = {
    "pass_all": "全部通过",
    "syntax_error": "语法错误",
    "truncation_or_repetition": "代码截断/重复生成",
    "function_name_mismatch": "函数名不匹配",
    "import_error": "导入错误",
    "type_error": "类型错误",
    "boundary_error": "边界条件错误",
    "assertion_failure": "逻辑错误(断言失败)",
    "attribute_error": "属性错误",
    "timeout": "运行超时",
    "partial_pass": "部分测试通过",
    "other_runtime": "其他运行时错误",
    "no_tests": "无测试用例",
}

IMPROVEMENT_HINTS_ZH = {
    "pass_all": "保持当前策略，可作为正例加入训练集。",
    "syntax_error": "增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。",
    "truncation_or_repetition": "增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。",
    "function_name_mismatch": "训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。",
    "import_error": "补充常用标准库 import 示例；在 instruction 中说明可用库。",
    "type_error": "增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。",
    "boundary_error": "针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。",
    "assertion_failure": "核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。",
    "attribute_error": "检查是否误用对象属性或 API；补充相关 API 用法示例。",
    "timeout": "优化算法复杂度相关训练数据；评测可适当放宽 timeout 以区分 TLE vs 逻辑错。",
    "partial_pass": "分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。",
    "other_runtime": "人工抽查 stderr，归入更细类别后补充规则。",
    "no_tests": "检查 MBPP 数据与评测配置。",
}


@dataclass
class ErrorDetail:
    """单条样例的错误分类结果。"""
    category: str
    subcategory: str = ""
    message: str = ""
    expected_functions: list[str] = field(default_factory=list)
    defined_functions: list[str] = field(default_factory=list)
    stderr_snippet: str = ""
    failed_test_index: int | None = None


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 对象；不存在则返回空字典。"""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_cases(path: Path) -> list[dict[str, Any]]:
    """读取 mbpp_cases.jsonl。"""
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def extract_functions_from_code(code: str) -> list[str]:
    """从代码中提取定义的函数名。"""
    names: list[str] = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                names.append(node.name)
    except SyntaxError:
        names.extend(DEF_FUNC_RE.findall(code))
    return names


def extract_functions_from_tests(test_results: list[dict[str, Any]], reference_code: str) -> list[str]:
    """从测试/参考代码推断期望函数名。"""
    expected: set[str] = set()
    for node in extract_functions_from_code(reference_code):
        expected.add(node)
    for tr in test_results:
        stderr = tr.get("stderr", "")
        for match in ASSERT_FUNC_RE.finditer(stderr):
            expected.add(match.group(1))
    return sorted(expected)


def detect_truncation_or_repetition(code: str, predict_raw: str) -> tuple[bool, str]:
    """检测生成截断或重复模式。"""
    text = predict_raw or code
    if not text.strip():
        return True, "empty_output"

    lines = code.splitlines()
    if lines:
        last = lines[-1].strip()
        if last and (
            last.count("(") > last.count(")")
            or last.count("[") > last.count("]")
            or last.count("{") > last.count("}")
        ):
            return True, "unclosed_bracket_at_eof"

    for line in lines:
        stripped = line.strip()
        if len(stripped) > 120:
            tokens = re.findall(r"\w+", stripped)
            if tokens:
                most_common = Counter(tokens).most_common(1)[0]
                if most_common[1] >= 8 and most_common[1] / len(tokens) > 0.35:
                    return True, "repetitive_tokens"

    if len(text) > 800 and text[-200:].count(text[-40:-20]) > 3:
        return True, "repeated_suffix"

    return False, ""


def classify_stderr(stderr: str, error_type: str) -> str:
    """根据 stderr 粗分运行时错误子类。"""
    if error_type == "timeout":
        return "timeout"
    if not stderr:
        return "other_runtime"

    checks = [
        ("import_error", ("ModuleNotFoundError", "ImportError")),
        ("type_error", ("TypeError",)),
        ("boundary_error", ("IndexError", "KeyError", "ValueError", "ZeroDivisionError")),
        ("attribute_error", ("AttributeError",)),
        ("assertion_failure", ("AssertionError",)),
        ("syntax_error", ("SyntaxError", "IndentationError")),
        ("function_name_mismatch", ("NameError",)),
    ]
    for category, markers in checks:
        if any(marker in stderr for marker in markers):
            return category
    return "other_runtime"


def pick_primary_failure(test_results: list[dict[str, Any]]) -> tuple[int | None, dict[str, Any] | None]:
    """选取首个失败测试作为主因。"""
    for idx, tr in enumerate(test_results):
        if not tr.get("passed"):
            return idx, tr
    return None, None


def classify_case(case: dict[str, Any]) -> ErrorDetail:
    """对单条 case 归入错误类别。"""
    code = case.get("code", "") or ""
    predict_raw = case.get("predict", "") or ""
    test_results = case.get("test_results", []) or []
    reference_code = case.get("reference_code", "") or ""
    total_tests = int(case.get("total_tests", 0) or 0)
    passed_tests = int(case.get("passed_tests", 0) or 0)
    syntax_ok = bool(case.get("syntax_ok", False))
    passed = bool(case.get("passed", False))

    expected_funcs = extract_functions_from_tests(test_results, reference_code)
    defined_funcs = extract_functions_from_code(code) if code else []

    if total_tests == 0:
        return ErrorDetail(category="no_tests", expected_functions=expected_funcs, defined_functions=defined_funcs)

    if passed:
        return ErrorDetail(category="pass_all", expected_functions=expected_funcs, defined_functions=defined_funcs)

    if not syntax_ok:
        is_trunc, sub = detect_truncation_or_repetition(code, predict_raw)
        if is_trunc:
            return ErrorDetail(
                category="truncation_or_repetition",
                subcategory=sub,
                expected_functions=expected_funcs,
                defined_functions=defined_funcs,
            )
        return ErrorDetail(
            category="syntax_error",
            subcategory=sub or "ast_parse_failed",
            expected_functions=expected_funcs,
            defined_functions=defined_funcs,
        )

    fail_idx, fail_tr = pick_primary_failure(test_results)
    stderr = (fail_tr or {}).get("stderr", "") if fail_tr else ""
    error_type = (fail_tr or {}).get("error_type", "") if fail_tr else ""

    category = classify_stderr(stderr, error_type)

    if category == "function_name_mismatch" and expected_funcs and defined_funcs:
        if not any(exp in defined_funcs for exp in expected_funcs):
            subcategory = "defined_vs_expected"
        else:
            category = "other_runtime"
            subcategory = "name_error_other"
    elif category == "function_name_mismatch" and expected_funcs and not defined_funcs:
        subcategory = "no_function_defined"
    elif category == "function_name_mismatch":
        subcategory = "name_not_found"
    else:
        subcategory = ""

    if passed_tests > 0 and not passed:
        if category == "assertion_failure":
            primary = "partial_pass"
        else:
            primary = category
        return ErrorDetail(
            category=primary,
            subcategory=subcategory or "partial",
            message=f"{passed_tests}/{total_tests} tests passed",
            expected_functions=expected_funcs,
            defined_functions=defined_funcs,
            stderr_snippet=stderr[-500:],
            failed_test_index=fail_idx,
        )

    return ErrorDetail(
        category=category,
        subcategory=subcategory,
        expected_functions=expected_funcs,
        defined_functions=defined_funcs,
        stderr_snippet=stderr[-500:],
        failed_test_index=fail_idx,
    )


def build_report(
    cases: list[dict[str, Any]],
    metrics: dict[str, Any],
    source_cases: Path,
    source_metrics: Path | None,
) -> dict[str, Any]:
    """汇总分类统计，生成结构化报告字典。"""
    category_counts: Counter[str] = Counter()
    subcategory_counts: Counter[str] = Counter()
    partial_pass_count = 0
    enriched_cases: list[dict[str, Any]] = []

    for case in cases:
        detail = classify_case(case)
        category_counts[detail.category] += 1
        if detail.subcategory:
            subcategory_counts[f"{detail.category}/{detail.subcategory}"] += 1
        if case.get("passed_tests", 0) > 0 and not case.get("passed"):
            partial_pass_count += 1

        enriched = {
            **case,
            "error_category": detail.category,
            "error_category_zh": CATEGORY_LABELS_ZH.get(detail.category, detail.category),
            "error_subcategory": detail.subcategory,
            "expected_functions": detail.expected_functions,
            "defined_functions": detail.defined_functions,
            "stderr_snippet": detail.stderr_snippet,
            "failed_test_index": detail.failed_test_index,
            "improvement_hint": IMPROVEMENT_HINTS_ZH.get(detail.category, ""),
        }
        enriched_cases.append(enriched)

    total = len(cases)
    failed = total - category_counts.get("pass_all", 0)

    category_stats = []
    for cat in ERROR_CATEGORIES:
        count = category_counts.get(cat, 0)
        if count == 0 and cat not in category_counts:
            continue
        category_stats.append(
            {
                "category": cat,
                "label_zh": CATEGORY_LABELS_ZH.get(cat, cat),
                "count": count,
                "ratio_in_all": round(count / total, 4) if total else 0.0,
                "ratio_in_failed": round(count / failed, 4) if failed else 0.0,
                "improvement_hint": IMPROVEMENT_HINTS_ZH.get(cat, ""),
            }
        )

    category_stats.sort(key=lambda x: x["count"], reverse=True)

    top_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in enriched_cases:
        cat = item["error_category"]
        if cat == "pass_all":
            continue
        if len(top_examples[cat]) < 3:
            top_examples[cat].append(
                {
                    "task_id": item.get("task_id"),
                    "prompt": (item.get("prompt") or "")[:200],
                    "defined_functions": item.get("defined_functions"),
                    "expected_functions": item.get("expected_functions"),
                    "code_preview": (item.get("code") or "")[:300],
                    "stderr_snippet": item.get("stderr_snippet", "")[:300],
                    "passed_tests": item.get("passed_tests"),
                    "total_tests": item.get("total_tests"),
                }
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "cases_file": str(source_cases),
            "metrics_file": str(source_metrics) if source_metrics else None,
        },
        "summary": {
            "num_cases_analyzed": total,
            "num_passed": category_counts.get("pass_all", 0),
            "num_failed": failed,
            "partial_pass_cases": partial_pass_count,
            "pass_at_1_from_metrics": metrics.get("pass_at_1"),
            "syntax_pass_rate_from_metrics": metrics.get("syntax_pass_rate"),
            "note": (
                "Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). "
                "Compare num_cases_analyzed with metrics num_tasks for coverage."
            ),
        },
        "category_distribution": category_stats,
        "subcategory_distribution": [
            {"key": k, "count": v} for k, v in subcategory_counts.most_common()
        ],
        "top_examples_by_category": dict(top_examples),
        "actionable_priorities": build_priorities(category_stats, failed),
        "cases": enriched_cases,
    }


def build_priorities(category_stats: list[dict[str, Any]], failed: int) -> list[dict[str, Any]]:
    """按失败占比排出优先改进项。"""
    priorities = []
    for item in category_stats:
        if item["category"] == "pass_all":
            continue
        impact = item["ratio_in_failed"]
        if impact >= 0.4:
            priority = "P0"
        elif impact >= 0.15:
            priority = "P1"
        elif impact >= 0.05:
            priority = "P2"
        else:
            priority = "P3"
        priorities.append(
            {
                "priority": priority,
                "category": item["category"],
                "label_zh": item["label_zh"],
                "count": item["count"],
                "share_of_failures": item["ratio_in_failed"],
                "recommended_action": item["improvement_hint"],
            }
        )
    return priorities


def render_markdown(report: dict[str, Any]) -> str:
    """将报告渲染为 Markdown 文本。"""
    s = report["summary"]
    lines = [
        "# 代码任务错误分析报告",
        "",
        f"- 生成时间(UTC): {report['generated_at']}",
        f"- 数据来源: `{report['source']['cases_file']}`",
        f"- 分析样本数: **{s['num_cases_analyzed']}**（通过 {s['num_passed']}，失败 {s['num_failed']}）",
        f"- 部分通过用例: {s['partial_pass_cases']}",
    ]
    if s.get("pass_at_1_from_metrics") is not None:
        lines.append(f"- 全量 pass@1 (metrics): **{s['pass_at_1_from_metrics']:.2%}**")
    if s.get("syntax_pass_rate_from_metrics") is not None:
        lines.append(f"- 全量语法通过率 (metrics): **{s['syntax_pass_rate_from_metrics']:.2%}**")
    lines.extend(["", "> " + s["note"], ""])

    lines.extend(["## 错误类型分布", "", "| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |", "|------|------|--------|--------|----------|"])
    for item in report["category_distribution"]:
        if item["category"] == "pass_all":
            continue
        lines.append(
            f"| {item['label_zh']} | {item['count']} | {item['ratio_in_all']:.1%} | "
            f"{item['ratio_in_failed']:.1%} | {item['improvement_hint'][:60]}... |"
            if len(item["improvement_hint"]) > 60
            else f"| {item['label_zh']} | {item['count']} | {item['ratio_in_all']:.1%} | "
            f"{item['ratio_in_failed']:.1%} | {item['improvement_hint']} |"
        )

    lines.extend(["", "## 优先改进项 (按失败占比)", ""])
    for p in report["actionable_priorities"][:6]:
        lines.append(
            f"- **{p['priority']} {p['label_zh']}**: {p['count']} 例 "
            f"({p['share_of_failures']:.1%} 失败) — {p['recommended_action']}"
        )

    lines.extend(["", "## 典型样例", ""])
    for cat, examples in report["top_examples_by_category"].items():
        label = CATEGORY_LABELS_ZH.get(cat, cat)
        lines.append(f"### {label} ({cat})")
        for ex in examples:
            lines.append(f"- task_id={ex['task_id']}: 定义 `{ex.get('defined_functions')}` vs 期望 `{ex.get('expected_functions')}`")
            if ex.get("stderr_snippet"):
                lines.append(f"  - stderr: `{ex['stderr_snippet'][:120].replace(chr(10), ' ')}`")
        lines.append("")

    lines.extend(
        [
            "## 如何据此提升准确率",
            "",
            "1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。",
            "2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。",
            "3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。",
            "4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。",
            "5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """读 cases，分类，写出 md/json/enriched jsonl。"""
    parser = argparse.ArgumentParser(description="Analyze MBPP evaluation errors from mbpp_cases.jsonl")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Path to mbpp_cases.jsonl")
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS, help="Optional mbpp_metrics.json")
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for reports")
    parser.add_argument("--tag", default="", help="Optional run tag for output filenames")
    args = parser.parse_args()

    if not args.cases.exists():
        raise FileNotFoundError(f"Cases file not found: {args.cases}")

    cases = load_cases(args.cases)
    metrics = load_json(args.metrics) if args.metrics else {}
    args.output_dir.mkdir(parents=True, exist_ok=True)

    tag = f"_{args.tag}" if args.tag else ""
    report = build_report(cases, metrics, args.cases, args.metrics if args.metrics and args.metrics.exists() else None)

    # Split full cases from summary report for smaller JSON
    full_cases = report.pop("cases")

    json_path = args.output_dir / f"error_analysis{tag}.json"
    md_path = args.output_dir / f"error_analysis{tag}.md"
    cases_path = args.output_dir / f"error_cases_enriched{tag}.jsonl"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with md_path.open("w", encoding="utf-8") as f:
        f.write(render_markdown({**report, "cases": []}))

    with cases_path.open("w", encoding="utf-8") as f:
        for item in full_cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Analyzed {len(cases)} cases")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {cases_path}")
    print("\nTop failure categories:")
    for item in report["category_distribution"][:5]:
        if item["category"] != "pass_all":
            print(f"  - {item['label_zh']}: {item['count']} ({item['ratio_in_failed']:.1%} of failures)")


if __name__ == "__main__":
    main()
