#!/usr/bin/env python3
"""
功能: 为 lora2 实验准备/链接训练与评测数据到本目录 data/。

输入: 上游 sft/data 或指定源
输出: lora2_exp_cgh/data/ 下数据集与 dataset_info.json
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    """准备数据目录并写出注册信息。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", type=Path, required=True)
    parser.add_argument("--source-data-dir", type=Path, default=Path("sft/data"))
    parser.add_argument("--mbpp-dir", type=Path, default=Path("/root/siton-tmp/mbpp"))
    args = parser.parse_args()

    exp_dir = args.exp_dir.resolve()
    project_root = exp_dir.parent.parent
    source_dir = (project_root / args.source_data_dir).resolve()
    data_dir = exp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    needed = [
        "code_sft_train.json",
        "code_sft_valid.json",
        "mbpp_sanitized_test.json",
    ]

    # 确保 MBPP json 存在
    mbpp_json = source_dir / "mbpp_sanitized_test.json"
    if not mbpp_json.exists():
        import subprocess

        subprocess.run(
            [
                "python3",
                str(project_root / "sft/scripts/prepare_mbpp_sanitized_data.py"),
                "--mbpp_dir",
                str(args.mbpp_dir),
                "--output_dir",
                str(source_dir),
            ],
            check=True,
        )

    for name in needed:
        src = source_dir / name
        dst = data_dir / name
        if not src.exists():
            raise FileNotFoundError(f"Missing source data file: {src}")
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)

    dataset_info = {
        "code_sft_train": {"file_name": "code_sft_train.json"},
        "code_sft_valid": {"file_name": "code_sft_valid.json"},
        "mbpp_sanitized_test": {"file_name": "mbpp_sanitized_test.json"},
    }
    info_path = data_dir / "dataset_info.json"
    info_path.write_text(json.dumps(dataset_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Prepared data dir -> {data_dir}")
    print(f"  dataset_info: {info_path}")


if __name__ == "__main__":
    main()
