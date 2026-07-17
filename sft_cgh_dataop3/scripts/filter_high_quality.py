#!/usr/bin/env python3
"""Filter code SFT data for high-quality, efficient fine-tuning.

Dimensions:
  1) syntax parsability (ast.parse)
  2) output length
  3) task completeness (function def, non-stub, brackets, trailing)
  4) duplication (exact / instruction / code fingerprint)
  5) task-type balance (stratified downsample)

Reads sft/data/*.json (read-only). Writes only under sft_cgh_dataop/.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


FENCE_RE = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)
BOUNDARY_RE = re.compile(
    r"\b(empty|none|null|edge|boundary|zero|single|optional|type|isinstance)\b",
    re.IGNORECASE,
)
INCOMPLETE_TAIL_RE = re.compile(
    r"^\s*(def|class|if|elif|else|for|while|try|except|finally|with)\b.*:\s*$"
)

TASK_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("string", ["string", "str", "substring", "palindrome", "vowel", "char", "word", "text"]),
    ("list_array", ["list", "array", "sort", "matrix", "tuple", "sequence", "element"]),
    ("math_number", ["number", "integer", "prime", "sum", "factorial", "gcd", "lcm", "digit", "math", "volume", "square", "fibonacci"]),
    ("dict_set", ["dict", "dictionary", "set", "map", "hash", "frequency", "counter"]),
    ("algo_search", ["search", "binary", "dfs", "bfs", "recursive", "dynamic", " knapsack", "dp ", "algorithm"]),
    ("file_io", ["file", "read", "write", "csv", "json", "path", "open("]),
    ("class_oop", ["class ", "object", "method", "self.", "oop"]),
    ("regex", ["regex", "regular expression", "re.", "pattern match"]),
    ("date_time", ["date", "time", "datetime", "day", "month", "year", "calendar"]),
]


@dataclass
class FilterConfig:
    min_output_chars: int = 60
    max_output_chars: int = 2500
    prefer_output_min: int = 80
    prefer_output_max: int = 1200
    require_function_def: bool = True
    reject_stub_only: bool = True
    require_balanced_brackets: bool = True
    reject_trailing_incomplete: bool = True
    dedup_exact: bool = True
    dedup_instruction: bool = True
    dedup_code_fingerprint: bool = True
    enable_balance: bool = True
    target_train_size: int = 6000
    max_per_type: int = 0
    min_per_type: int = 50
    seed: int = 42
    splits: dict[str, str] = field(
        default_factory=lambda: {
            "train": "code_sft_train.json",
            "valid": "code_sft_valid.json",
            "test": "code_sft_test.json",
        }
    )
    balance_splits: list[str] = field(default_factory=lambda: ["train"])


@dataclass
class SampleMeta:
    index: int
    instruction: str
    input: str
    output: str
    code: str
    task_type: str
    quality_score: float
    output_len: int
    reject_reason: str | None = None


def load_yaml_config(path: Path | None) -> FilterConfig:
    cfg = FilterConfig()
    if path is None or not path.exists():
        return cfg
    try:
        import yaml  # type: ignore
    except ImportError:
        # Minimal YAML subset: key: value lines (enough for our config)
        text = path.read_text(encoding="utf-8")
        data: dict[str, Any] = {}
        current_list_key: str | None = None
        current_map_key: str | None = None
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            if line.startswith("  - ") and current_list_key:
                data.setdefault(current_list_key, []).append(line.strip()[2:].strip())
                continue
            if line.startswith("  ") and current_map_key and ":" in line:
                k, v = line.strip().split(":", 1)
                data.setdefault(current_map_key, {})[k.strip()] = v.strip().strip('"')
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                if key in ("splits",):
                    current_map_key = key
                    current_list_key = None
                    data[key] = {}
                elif key in ("balance_splits",):
                    current_list_key = key
                    current_map_key = None
                    data[key] = []
                else:
                    current_list_key = None
                    current_map_key = None
                continue
            current_list_key = None
            current_map_key = None
            if val.lower() in ("true", "false"):
                data[key] = val.lower() == "true"
            else:
                try:
                    data[key] = int(val)
                except ValueError:
                    data[key] = val.strip('"')
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for k, v in data.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


def extract_code(text: str) -> str:
    text = (text or "").strip()
    match = FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


def balanced_brackets(code: str) -> bool:
    """Bracket balance with string/comment awareness.

    If ``ast.parse`` already succeeded, this is mostly a safety net for
    fence-extraction edge cases; triple quotes must be handled correctly.
    """
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    in_str: str | None = None
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if in_str:
            if len(in_str) == 1 and ch == "\\" and i + 1 < n:
                i += 2
                continue
            if len(in_str) == 3:
                if code[i : i + 3] == in_str:
                    in_str = None
                    i += 3
                    continue
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"'):
            if code[i : i + 3] in ("'''", '"""'):
                in_str = code[i : i + 3]
                i += 3
                continue
            in_str = ch
            i += 1
            continue
        if ch == "#":
            while i < n and code[i] != "\n":
                i += 1
            continue
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch in pairs.values():
            if not stack or stack[-1] != ch:
                return False
            stack.pop()
        i += 1
    return not stack and in_str is None


def trailing_incomplete(code: str) -> bool:
    lines = [ln for ln in code.splitlines() if ln.strip()]
    if not lines:
        return True
    last = lines[-1].rstrip()
    if last.endswith("\\"):
        return True
    if INCOMPLETE_TAIL_RE.match(last):
        return True
    if last.strip() in ("...", "....", "....."):
        return True
    return False


def has_non_stub_function(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        real_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Pass):
                continue
            if isinstance(stmt, ast.Expr):
                val = stmt.value
                if isinstance(val, ast.Constant):
                    if val.value is Ellipsis:
                        continue
                    if isinstance(val.value, str):  # docstring
                        continue
                if isinstance(val, ast.Ellipsis):  # py<3.8 style unlikely
                    continue
            real_body.append(stmt)
        if real_body:
            return True
    return False


def has_docstring(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if ast.get_docstring(node):
                return True
    return False


def classify_task_type(instruction: str, code: str) -> str:
    blob = f"{instruction}\n{code}".lower()
    for name, keywords in TASK_TYPE_RULES:
        if any(k in blob for k in keywords):
            return name
    return "other"


def quality_score(meta: SampleMeta, cfg: FilterConfig, tree: ast.AST | None) -> float:
    score = 0.0
    if tree is not None and has_non_stub_function(tree):
        score += 2.0
    if tree is not None and has_docstring(tree):
        score += 1.0
    if cfg.prefer_output_min <= meta.output_len <= cfg.prefer_output_max:
        score += 1.0
    elif meta.output_len < cfg.min_output_chars or meta.output_len > cfg.max_output_chars:
        score -= 1.0
    if BOUNDARY_RE.search(meta.instruction):
        score += 1.0
    # Prefer moderate complexity: number of defs
    if tree is not None:
        n_defs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        if 1 <= n_defs <= 3:
            score += 0.5
    return score


def code_fingerprint(code: str) -> str:
    try:
        tree = ast.parse(code)
        normalized = ast.dump(tree, annotate_fields=False)
    except Exception:
        normalized = re.sub(r"\s+", "", code)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def evaluate_sample(index: int, row: dict[str, Any], cfg: FilterConfig) -> SampleMeta:
    instruction = str(row.get("instruction", "")).strip()
    input_text = str(row.get("input", "")).strip()
    output = str(row.get("output", "")).strip()
    code = extract_code(output)
    meta = SampleMeta(
        index=index,
        instruction=instruction,
        input=input_text,
        output=output,
        code=code,
        task_type="other",
        quality_score=0.0,
        output_len=len(output),
    )

    if not instruction:
        meta.reject_reason = "empty_instruction"
        return meta
    if not output:
        meta.reject_reason = "empty_output"
        return meta
    if meta.output_len < cfg.min_output_chars:
        meta.reject_reason = "output_too_short"
        return meta
    if meta.output_len > cfg.max_output_chars:
        meta.reject_reason = "output_too_long"
        return meta
    if not code.strip():
        meta.reject_reason = "empty_code"
        return meta

    try:
        tree = ast.parse(code)
    except SyntaxError:
        meta.reject_reason = "syntax_error"
        return meta

    if cfg.reject_trailing_incomplete and trailing_incomplete(code):
        meta.reject_reason = "trailing_incomplete"
        return meta

    has_def = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
    if cfg.require_function_def and not has_def:
        meta.reject_reason = "no_function_def"
        return meta
    if cfg.reject_stub_only and not has_non_stub_function(tree):
        meta.reject_reason = "stub_only"
        return meta

    meta.task_type = classify_task_type(instruction, code)
    meta.quality_score = quality_score(meta, cfg, tree)
    return meta


def deduplicate(metas: list[SampleMeta], cfg: FilterConfig) -> tuple[list[SampleMeta], Counter]:
    reasons: Counter = Counter()
    kept: list[SampleMeta] = []

    exact_seen: set[str] = set()
    instr_best: dict[str, SampleMeta] = {}
    code_seen: set[str] = set()

    # First pass: exact + code fingerprint in original order; track best per instruction
    candidates: list[SampleMeta] = []
    for meta in metas:
        if meta.reject_reason:
            continue
        if cfg.dedup_exact:
            key = hashlib.md5(
                f"{meta.instruction}\0{meta.input}\0{meta.output}".encode("utf-8")
            ).hexdigest()
            if key in exact_seen:
                reasons["exact_dup"] += 1
                continue
            exact_seen.add(key)
        if cfg.dedup_code_fingerprint:
            fp = code_fingerprint(meta.code)
            if fp in code_seen:
                reasons["code_fingerprint_dup"] += 1
                continue
            code_seen.add(fp)
        candidates.append(meta)

    if not cfg.dedup_instruction:
        return candidates, reasons

    for meta in candidates:
        ikey = meta.instruction.lower()
        prev = instr_best.get(ikey)
        if prev is None or meta.quality_score > prev.quality_score:
            if prev is not None:
                reasons["instruction_dup"] += 1
            instr_best[ikey] = meta
        else:
            reasons["instruction_dup"] += 1

    # Preserve relative order of winners
    winners = {id(v) for v in instr_best.values()}
    kept = [m for m in candidates if id(m) in winners]
    return kept, reasons


def balance_by_type(metas: list[SampleMeta], cfg: FilterConfig) -> tuple[list[SampleMeta], dict[str, Any]]:
    by_type: dict[str, list[SampleMeta]] = defaultdict(list)
    for m in metas:
        by_type[m.task_type].append(m)

    for t in by_type:
        by_type[t].sort(key=lambda x: (-x.quality_score, x.index))

    types = sorted(by_type.keys())
    n_types = max(len(types), 1)
    if cfg.max_per_type > 0:
        cap = cfg.max_per_type
    elif cfg.target_train_size > 0:
        cap = max(cfg.min_per_type, int(cfg.target_train_size / n_types * 1.5))
    else:
        cap = max(len(metas), 1)

    rng = random.Random(cfg.seed)
    selected: list[SampleMeta] = []
    per_type_kept: dict[str, int] = {}
    for t in types:
        pool = by_type[t]
        # Keep top by quality within cap; slight shuffle among equal scores for diversity
        if len(pool) <= cap:
            chosen = pool
        else:
            # Take top 80% by score deterministically, fill rest randomly from remainder
            hard_n = int(cap * 0.8)
            head = pool[:hard_n]
            rest = pool[hard_n:]
            need = cap - len(head)
            rng.shuffle(rest)
            chosen = head + rest[:need]
        selected.extend(chosen)
        per_type_kept[t] = len(chosen)

    # If still above global target, trim lowest scores globally
    if cfg.target_train_size > 0 and len(selected) > cfg.target_train_size:
        selected.sort(key=lambda x: (-x.quality_score, x.index))
        selected = selected[: cfg.target_train_size]
        per_type_kept = Counter(m.task_type for m in selected)

    selected.sort(key=lambda x: x.index)
    info = {
        "cap_per_type": cap,
        "before_by_type": {t: len(by_type[t]) for t in types},
        "after_by_type": dict(per_type_kept),
        "before_total": len(metas),
        "after_total": len(selected),
    }
    return selected, info


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON in {path}")
    return data


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def rows_from_metas(metas: list[SampleMeta]) -> list[dict[str, str]]:
    return [
        {"instruction": m.instruction, "input": m.input, "output": m.output}
        for m in metas
    ]


def process_split(
    name: str,
    rows: list[dict[str, Any]],
    cfg: FilterConfig,
    do_balance: bool,
) -> dict[str, Any]:
    hard_reject: Counter = Counter()
    metas: list[SampleMeta] = []
    for i, row in enumerate(rows):
        meta = evaluate_sample(i, row, cfg)
        if meta.reject_reason:
            hard_reject[meta.reject_reason] += 1
        metas.append(meta)

    passed = [m for m in metas if m.reject_reason is None]
    deduped, dedup_reasons = deduplicate(passed, cfg)

    balance_info: dict[str, Any] | None = None
    final = deduped
    if do_balance and cfg.enable_balance:
        final, balance_info = balance_by_type(deduped, cfg)

    type_before = Counter(m.task_type for m in passed)
    type_after = Counter(m.task_type for m in final)

    return {
        "split": name,
        "input_count": len(rows),
        "hard_pass": len(passed),
        "after_dedup": len(deduped),
        "final_count": len(final),
        "keep_ratio": round(len(final) / max(len(rows), 1), 4),
        "hard_reject_reasons": dict(hard_reject),
        "dedup_reasons": dict(dedup_reasons),
        "task_type_before_balance": dict(type_before),
        "task_type_after": dict(type_after),
        "balance": balance_info,
        "metas": final,
        "mean_quality": round(
            sum(m.quality_score for m in final) / max(len(final), 1), 3
        ),
        "mean_output_len": round(
            sum(m.output_len for m in final) / max(len(final), 1), 1
        ),
    }


def render_report(results: list[dict[str, Any]], cfg: FilterConfig) -> str:
    lines = [
        "# 高质量数据筛选报告",
        "",
        "依据错误分析中的 P0/P1/P2 失败模式，按语法可解析性、输出长度、任务完整性、重复率、任务类型均衡性筛选。",
        "",
        "## 配置摘要",
        "",
        f"- 输出长度: [{cfg.min_output_chars}, {cfg.max_output_chars}]",
        f"- 要求函数定义: {cfg.require_function_def}；拒绝 stub: {cfg.reject_stub_only}",
        f"- 去重: exact={cfg.dedup_exact}, instruction={cfg.dedup_instruction}, code_fp={cfg.dedup_code_fingerprint}",
        f"- 均衡抽样: enable={cfg.enable_balance}, target_train_size={cfg.target_train_size}",
        f"- seed: {cfg.seed}",
        "",
    ]
    for r in results:
        lines.extend(
            [
                f"## Split: `{r['split']}`",
                "",
                f"| 阶段 | 数量 |",
                f"|------|------|",
                f"| 输入 | {r['input_count']} |",
                f"| 硬过滤通过 | {r['hard_pass']} |",
                f"| 去重后 | {r['after_dedup']} |",
                f"| **最终保留** | **{r['final_count']}** ({r['keep_ratio']:.1%}) |",
                f"| 平均质量分 | {r['mean_quality']} |",
                f"| 平均 output 长度 | {r['mean_output_len']} |",
                "",
                "### 硬过滤拒绝原因",
                "",
            ]
        )
        if r["hard_reject_reasons"]:
            lines.append("| 原因 | 数量 |")
            lines.append("|------|------|")
            for k, v in sorted(r["hard_reject_reasons"].items(), key=lambda x: -x[1]):
                lines.append(f"| {k} | {v} |")
        else:
            lines.append("_无_")
        lines.append("")
        lines.append("### 去重")
        lines.append("")
        if r["dedup_reasons"]:
            lines.append("| 原因 | 数量 |")
            lines.append("|------|------|")
            for k, v in sorted(r["dedup_reasons"].items(), key=lambda x: -x[1]):
                lines.append(f"| {k} | {v} |")
        else:
            lines.append("_无显著重复_")
        lines.append("")
        lines.append("### 任务类型分布（最终）")
        lines.append("")
        lines.append("| 类型 | 数量 |")
        lines.append("|------|------|")
        for k, v in sorted(r["task_type_after"].items(), key=lambda x: -x[1]):
            lines.append(f"| {k} | {v} |")
        lines.append("")
    lines.extend(
        [
            "## 与错误分析的对应关系",
            "",
            "- `syntax_error` / `no_function_def` / `trailing_incomplete` → 压低评测中的语法错误与空定义",
            "- 强制 `def` + 非 stub → 强化函数命名与完整实现，缓解 function_name_mismatch / partial_pass",
            "- 类型均衡 + 边界词加分 → 服务 P0 逻辑题与 P2 类型/边界错误",
            "- 去重 + 控规模 → 用更少样本做高效 SFT，减少多数类过拟合",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source_dir",
        type=Path,
        default=Path("/root/siton-tmp/assignment_A/sft/data"),
        help="Read-only source directory with code_sft_*.json",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("/root/siton-tmp/assignment_A/sft_cgh_dataop/data"),
    )
    parser.add_argument(
        "--report_dir",
        type=Path,
        default=Path("/root/siton-tmp/assignment_A/sft_cgh_dataop/outputs/filter"),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/root/siton-tmp/assignment_A/sft_cgh_dataop/configs/filter_config.yaml"),
    )
    parser.add_argument("--target_train_size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    if args.target_train_size is not None:
        cfg.target_train_size = args.target_train_size
    if args.seed is not None:
        cfg.seed = args.seed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    registry: dict[str, Any] = {}

    for split, filename in cfg.splits.items():
        src = args.source_dir / filename
        if not src.exists():
            raise FileNotFoundError(f"Missing source split: {src}")
        rows = load_rows(src)
        do_balance = split in set(cfg.balance_splits)
        result = process_split(split, rows, cfg, do_balance=do_balance)
        out_name = filename.replace(".json", "_hq.json")
        out_path = args.output_dir / out_name
        save_json(out_path, rows_from_metas(result["metas"]))
        ds_key = out_name.replace(".json", "")
        registry[ds_key] = {"file_name": out_name}
        # drop heavy metas before report dump
        slim = {k: v for k, v in result.items() if k != "metas"}
        results.append(slim)
        print(
            f"[{split}] {result['input_count']} -> {result['final_count']} "
            f"({result['keep_ratio']:.1%}) -> {out_path}"
        )

    # Also register aliases expected by train yaml
    if "code_sft_train_hq" in registry:
        registry["code_sft_train_hq"] = registry["code_sft_train_hq"]
    if "code_sft_valid_hq" in registry:
        registry["code_sft_valid_hq"] = registry["code_sft_valid_hq"]

    save_json(args.output_dir / "dataset_info.json", registry)

    report_md = render_report(results, cfg)
    (args.report_dir / "filter_report.md").write_text(report_md, encoding="utf-8")
    save_json(
        args.report_dir / "filter_report.json",
        {"config": asdict(cfg), "splits": results},
    )
    print(f"Wrote report -> {args.report_dir / 'filter_report.md'}")
    print(f"Wrote registry -> {args.output_dir / 'dataset_info.json'}")


if __name__ == "__main__":
    main()
