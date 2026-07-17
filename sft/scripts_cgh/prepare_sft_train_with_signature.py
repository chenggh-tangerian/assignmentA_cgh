#!/usr/bin/env python3
"""
功能: 对 SFT train/valid/test JSON 的 instruction 注入函数签名。

输入:  --source_dir  含 code_sft_{train,valid,test}.json
输出:  --output_dir  code_sft_*_with_signature.json 并更新 dataset_info.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from signature_utils import augment_row, normalize_text
DEFAULT_SOURCE_DIR = SCRIPT_DIR.parent / "data_cgh"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "data_cgh"

SPLITS = ("train", "valid", "test")


def load_json(path: Path) -> list[dict[str, Any]]:
    """读取 JSON 列表。"""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, rows: list[dict[str, Any]]) -> None:
    """写出 UTF-8 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


def convert_split(
    source_path: Path,
    output_path: Path,
    *,
    drop_without_signature: bool,
) -> dict[str, int]:
    """转换单个 split，返回统计计数。"""
    rows = load_json(source_path)
    converted: list[dict[str, Any]] = []
    augmented = 0
    kept_plain = 0
    skipped = 0

    for row in rows:
        item = augment_row(row, drop_without_signature=drop_without_signature)
        if item is None:
            skipped += 1
            continue
        converted.append(item)
        signature_used = "You must implement the solution using exactly this function signature" in item["instruction"]
        if signature_used:
            augmented += 1
        else:
            kept_plain += 1

    save_json(output_path, converted)
    return {
        "source_rows": len(rows),
        "output_rows": len(converted),
        "augmented_with_signature": augmented,
        "kept_without_signature": kept_plain,
        "skipped": skipped,
    }


def main() -> None:
    """批量处理 train/valid/test 并注册数据集。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--drop-no-signature",
        action="store_true",
        help="Drop rows whose output has no extractable def signature.",
    )
    args = parser.parse_args()

    stats: dict[str, dict[str, int]] = {}
    dataset_info: dict[str, dict[str, str]] = {}

    for split in SPLITS:
        source_name = f"code_sft_{split}.json"
        output_name = f"code_sft_{split}_with_signature.json"
        source_path = args.source_dir / source_name
        output_path = args.output_dir / output_name
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source split: {source_path}")

        stats[split] = convert_split(
            source_path,
            output_path,
            drop_without_signature=args.drop_no_signature,
        )
        dataset_info[f"code_sft_{split}_with_signature"] = {"file_name": output_name}
        print(
            f"{split}: {stats[split]['source_rows']} -> {stats[split]['output_rows']} "
            f"(signature={stats[split]['augmented_with_signature']}, "
            f"plain={stats[split]['kept_without_signature']}, "
            f"skipped={stats[split]['skipped']})"
        )
        print(f"  wrote {output_path}")

    mbpp_eval_name = "mbpp_sanitized_test_with_signature.json"
    dataset_info["mbpp_sanitized_test_with_signature"] = {"file_name": mbpp_eval_name}

    info_path = args.output_dir / "dataset_info.json"
    with info_path.open("w", encoding="utf-8") as f:
        json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Wrote {info_path}")

    preview_path = args.output_dir / "code_sft_train_with_signature.json"
    preview_rows = load_json(preview_path)
    for row in preview_rows:
        if "function signature" in row["instruction"]:
            print("\nExample augmented instruction tail:")
            print(row["instruction"][-240:])
            break


if __name__ == "__main__":
    main()
