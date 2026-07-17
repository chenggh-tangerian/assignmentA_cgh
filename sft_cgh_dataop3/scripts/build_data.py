#!/usr/bin/env python3
"""Build sft_cgh_dataop3 data: soft filter + signature + light train-only upsample.

HARD RULES:
  - Source ONLY sft/data/code_sft_*.json
  - NEVER read MBPP / cases / reference_code / error enriched files for training
  - Target ~60% of original train size (soft pool + light extras)
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


MODULE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MODULE_DIR.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
SFT_SCRIPTS_CGH = PROJECT_ROOT / "sft" / "scripts_cgh"

FORBIDDEN_NAME_PARTS = (
    "mbpp_cases",
    "error_cases_enriched",
    "failure_augment",
)

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SFT_SCRIPTS_CGH))

from filter_high_quality import (  # noqa: E402
    load_yaml_config,
    process_split,
    save_json,
    SampleMeta,
)
from signature_utils import augment_row  # noqa: E402


BOUNDARY_RE = re.compile(
    r"\b(empty|none|null|edge|boundary|zero|single|optional|isinstance)\b",
    re.I,
)
TYPE_RE = re.compile(
    r"\b(int|str|list|dict|tuple|float|bool|isinstance|cast|type)\b",
    re.I,
)
ALGO_RE = re.compile(
    r"\b(sort|search|recursive|dynamic|prime|gcd|lcm|matrix|palindrome|binary|algorithm|fibonacci|knapsack)\b",
    re.I,
)


def assert_source_allowed(path: Path) -> None:
    text = str(path.resolve()).replace("\\", "/")
    if "/sft/data/" not in text and not text.endswith("/sft/data"):
        lower = text.lower()
        for bad in FORBIDDEN_NAME_PARTS:
            if bad in lower:
                raise RuntimeError(f"Refusing forbidden path: {path}")


def load_json(path: Path) -> list[dict[str, Any]]:
    assert_source_allowed(path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}")
    return data


def to_alpaca(row: dict[str, Any]) -> dict[str, str]:
    return {
        "instruction": str(row["instruction"]),
        "input": str(row.get("input", "")),
        "output": str(row["output"]),
    }


def inject_signature(row: dict[str, str]) -> dict[str, str] | None:
    item = augment_row(row, drop_without_signature=False)
    if item is None:
        return None
    return to_alpaca(item)


def tag_row(instruction: str, output: str) -> set[str]:
    blob = f"{instruction}\n{output}"
    tags: set[str] = set()
    if ALGO_RE.search(blob):
        tags.add("algo_like")
    if TYPE_RE.search(blob):
        tags.add("type_like")
    if BOUNDARY_RE.search(blob):
        tags.add("boundary_like")
    if not tags:
        tags.add("other")
    return tags


def select_train_near_60pct(
    metas: list[SampleMeta],
    *,
    target_total: int,
    seed: int,
    extra_algo: int = 200,
    extra_type: int = 150,
    extra_boundary: int = 100,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Keep almost all soft-filtered uniques, then light category extras from train only."""
    rng = random.Random(seed)
    ranked = sorted(metas, key=lambda m: (-m.quality_score, m.index))

    by_tag: dict[str, list[SampleMeta]] = defaultdict(list)
    for m in ranked:
        for t in tag_row(m.instruction, m.output):
            by_tag[t].append(m)

    # Base = all unique soft samples (already ~59% of raw)
    selected = list(ranked)
    selected_ids = {m.index for m in selected}

    extras: list[SampleMeta] = []

    def add_extra(tag: str, n: int) -> None:
        pool = [m for m in by_tag.get(tag, []) if m.index in selected_ids]
        extras.extend(pool[:n])

    add_extra("algo_like", extra_algo)
    add_extra("type_like", extra_type)
    add_extra("boundary_like", extra_boundary)

    combined = selected + extras
    if len(combined) > target_total:
        # Prefer keeping all uniques; trim extras first
        room = max(0, target_total - len(selected))
        combined = selected + extras[:room]
    # If still under target and we trimmed nothing, that's fine (~60%).

    rng.shuffle(combined)

    rows: list[dict[str, str]] = []
    sig_ok = 0
    for m in combined:
        item = inject_signature(
            {"instruction": m.instruction, "input": m.input, "output": m.output}
        )
        if item is None:
            continue
        rows.append(item)
        if "function signature" in item["instruction"]:
            sig_ok += 1

    tag_counts = Counter()
    for m in combined:
        for t in tag_row(m.instruction, m.output):
            tag_counts[t] += 1

    info = {
        "soft_pool": len(metas),
        "unique_selected": len(selected),
        "extras": len(combined) - len(selected),
        "final": len(rows),
        "with_signature": sig_ok,
        "tag_counts_in_final": dict(tag_counts),
        "quotas": {
            "extra_algo": extra_algo,
            "extra_type": extra_type,
            "extra_boundary": extra_boundary,
            "target_total": target_total,
        },
        "sources": ["sft/data/code_sft_train.json ONLY"],
        "forbidden_used": False,
    }
    return rows, info


def process_valid(metas: list[SampleMeta]) -> list[dict[str, str]]:
    """Keep all soft-filtered valid with signature (from sft/data only)."""
    ranked = sorted(metas, key=lambda m: (-m.quality_score, m.index))
    rows: list[dict[str, str]] = []
    for m in ranked:
        item = inject_signature(
            {"instruction": m.instruction, "input": m.input, "output": m.output}
        )
        if item:
            rows.append(item)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_dir", type=Path, default=PROJECT_ROOT / "sft" / "data")
    parser.add_argument("--output_dir", type=Path, default=MODULE_DIR / "data")
    parser.add_argument(
        "--filter_config",
        type=Path,
        default=MODULE_DIR / "configs" / "filter_config.yaml",
    )
    parser.add_argument("--report_dir", type=Path, default=MODULE_DIR / "outputs" / "filter")
    parser.add_argument(
        "--target_ratio",
        type=float,
        default=0.60,
        help="Target train size ≈ ratio * |sft/data train|",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    src = args.source_dir.resolve()
    if src != (PROJECT_ROOT / "sft" / "data").resolve():
        raise RuntimeError(f"source_dir must be sft/data, got {src}")

    cfg = load_yaml_config(args.filter_config)
    cfg.enable_balance = False
    cfg.target_train_size = 0
    cfg.balance_splits = []
    cfg.seed = args.seed

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    train_raw = load_json(src / "code_sft_train.json")
    target_total = max(1, int(round(len(train_raw) * args.target_ratio)))

    report: dict[str, Any] = {
        "constraint": "train_from_sft_data_only_no_test_leak",
        "source_dir": str(src),
        "target_ratio": args.target_ratio,
        "target_total": target_total,
    }

    train_result = process_split("train", train_raw, cfg, do_balance=False)
    train_rows, train_info = select_train_near_60pct(
        train_result["metas"],
        target_total=target_total,
        seed=args.seed,
    )
    save_json(args.output_dir / "code_sft_train.json", train_rows)
    report["train"] = {
        "input": len(train_raw),
        "soft_pass": train_result["hard_pass"],
        "after_dedup": train_result["after_dedup"],
        "ratio_vs_raw": round(len(train_rows) / len(train_raw), 4),
        **train_info,
    }
    print(
        f"[train] {len(train_raw)} -> soft {train_result['after_dedup']} "
        f"-> final {len(train_rows)} "
        f"({len(train_rows)/len(train_raw):.1%} of raw, target≈{args.target_ratio:.0%}/{target_total})"
    )

    valid_raw = load_json(src / "code_sft_valid.json")
    valid_result = process_split("valid", valid_raw, cfg, do_balance=False)
    valid_rows = process_valid(valid_result["metas"])
    save_json(args.output_dir / "code_sft_valid.json", valid_rows)
    report["valid"] = {
        "input": len(valid_raw),
        "soft_pass": valid_result["hard_pass"],
        "final": len(valid_rows),
    }
    print(f"[valid] {len(valid_raw)} -> soft {valid_result['hard_pass']} -> {len(valid_rows)}")

    # Predict-only copy (NOT mixed into train)
    mbpp_src = (
        PROJECT_ROOT
        / "sft"
        / "infer_signature_cgh"
        / "data"
        / "mbpp_sanitized_test_with_signature.json"
    )
    registry = {
        "code_sft_train": {"file_name": "code_sft_train.json"},
        "code_sft_valid": {"file_name": "code_sft_valid.json"},
    }
    if mbpp_src.exists():
        mbpp_dst = args.output_dir / "mbpp_sanitized_test_with_signature.json"
        mbpp_dst.write_bytes(mbpp_src.read_bytes())
        registry["mbpp_sanitized_test_with_signature"] = {
            "file_name": "mbpp_sanitized_test_with_signature.json"
        }
        report["eval_mbpp_copied_for_predict_only"] = str(mbpp_src)
        report["eval_mbpp_mixed_into_train"] = False

    save_json(args.output_dir / "dataset_info.json", registry)
    save_json(args.report_dir / "data_report.json", report)

    lines = [
        "# sft_cgh_dataop3 数据报告（公平，~60% 规模）",
        "",
        "## 约束",
        "- 训练样本 **只** 来自 `sft/data/code_sft_train.json`",
        "- **未** 将 MBPP / cases / reference 混入 train",
        f"- 目标规模 ≈ raw×{args.target_ratio:.0%} = {target_total}",
        f"- 最终 train = **{len(train_rows)}**（{len(train_rows)/len(train_raw):.1%} of raw）",
        "",
        "## Train",
        f"- 原始: {len(train_raw)}",
        f"- 软过滤+去重: {train_result['after_dedup']}",
        f"- 定向加码 extras: {train_info['extras']}",
        f"- 最终: {len(train_rows)}",
        f"- 签名注入: {train_info['with_signature']}",
        f"- 标签分布: {train_info['tag_counts_in_final']}",
        "",
        "## Valid",
        f"- 最终: {len(valid_rows)}（sft/data valid 软过滤全留）",
        "",
    ]
    (args.report_dir / "data_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.report_dir / 'data_report.md'}")


if __name__ == "__main__":
    main()
