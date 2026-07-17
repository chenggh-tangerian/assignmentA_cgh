#!/usr/bin/env python3
"""
功能: 清理 model 目录下多余 checkpoint，节省磁盘。

输入: model_dir、keep 数量、dry_run
输出: 删除多余 checkpoint 目录（或仅打印）
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


CKPT_RE = re.compile(r"^checkpoint-(\d+)$")


def checkpoint_step(path: Path) -> int:
    """从 checkpoint 目录名解析步数。"""
    m = CKPT_RE.match(path.name)
    return int(m.group(1)) if m else -1


def prune(model_dir: Path, keep: int = 0, dry_run: bool = False) -> list[str]:
    """keep=0 删除全部 checkpoint；keep=1 仅保留最新（断点续训用）。"""
    ckpts = sorted(
        [p for p in model_dir.iterdir() if p.is_dir() and CKPT_RE.match(p.name)],
        key=checkpoint_step,
    )
    if keep <= 0:
        to_remove = ckpts
    elif len(ckpts) <= keep:
        return []
    else:
        to_remove = ckpts[: len(ckpts) - keep]

    removed = []
    for p in to_remove:
        removed.append(p.name)
        if not dry_run:
            shutil.rmtree(p)
    return removed


def main() -> None:
    """CLI 入口执行清理。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--keep", type=int, default=0, help="保留最新 N 个 checkpoint；0=全删（训练成功后）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.model_dir.exists():
        print(f"skip: {args.model_dir} not found")
        return

    removed = prune(args.model_dir, keep=args.keep, dry_run=args.dry_run)
    if removed:
        action = "would remove" if args.dry_run else "removed"
        print(f"{action}: {', '.join(removed)} under {args.model_dir}")
    else:
        print(f"nothing to prune under {args.model_dir}")


if __name__ == "__main__":
    main()
