#!/usr/bin/env python3
"""
功能: 将 MBPP sanitized parquet 转为 LLaMA-Factory 可用的 JSON 评测/预测集。

输入:
  --mbpp_dir  MBPP 根目录 (默认 <project_parent>/mbpp)
  --config    配置名，如 sanitized
  --split     划分名，如 test

输出:
  {output_dir}/mbpp_{config}_{split}.json
  每条含 instruction / input / output / task_id
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MBPP_DIR = PROJECT_ROOT.parent / "mbpp"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "sft" / "data"


def read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    """读取 parquet 为字典列表。"""
    try:
        import pyarrow.parquet as pq

        return pq.read_table(path).to_pylist()
    except Exception:
        try:
            import pandas as pd

            return pd.read_parquet(path).to_dict("records")
        except Exception as exc:
            raise RuntimeError(f"Failed to read parquet file: {path}") from exc


def normalize_text(value: Any) -> str:
    """字段转字符串并去首尾空白。"""
    return str(value or "").strip()


def main() -> None:
    """读指定 MBPP split，转为 Alpaca 风格 JSON 并写出。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--mbpp_dir", type=Path, default=DEFAULT_MBPP_DIR)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--config", default="sanitized")
    parser.add_argument("--split", default="test")
    args = parser.parse_args()

    split_path = args.mbpp_dir / args.config / f"{args.split}-00000-of-00001.parquet"
    if not split_path.exists():
        raise FileNotFoundError(f"Missing MBPP split file: {split_path}")

    rows = read_parquet_rows(split_path)
    converted = []
    for row in rows:
        task_id = row.get("task_id")
        prompt = normalize_text(row.get("prompt") if args.config == "sanitized" else row.get("text"))
        code = normalize_text(row.get("code"))
        if not prompt or not code:
            continue

        converted.append(
            {
                "instruction": prompt,
                "input": "",
                "output": code,
                "task_id": int(task_id) if task_id is not None else len(converted),
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_file = args.output_dir / f"mbpp_{args.config}_{args.split}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Converted {len(converted)} rows from {split_path}")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
