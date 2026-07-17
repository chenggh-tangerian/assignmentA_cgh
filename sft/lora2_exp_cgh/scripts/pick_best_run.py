#!/usr/bin/env python3
"""
功能: 从网格 run 中按 pass@1 选出最优 run_id。

输入: grid run_id 列表、state 目录
输出: 打印/返回最优 run_id 与分数
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    """读取单个 run 状态 JSON。"""
    return json.loads(path.read_text(encoding="utf-8"))


def pick_best(grid_run_ids: list[str], state_dir: Path) -> tuple[str | None, float | None]:
    """在候选中选 pass@1 最高者。"""
    best_id: str | None = None
    best_pass: float | None = None

    for rid in grid_run_ids:
        state_path = state_dir / f"{rid}.json"
        if not state_path.exists():
            continue
        state = load_state(state_path)
        if state.get("stages", {}).get("eval", {}).get("status") != "done":
            continue
        pass_at_1 = state.get("metrics", {}).get("pass_at_1")
        if pass_at_1 is None:
            continue
        if best_pass is None or pass_at_1 > best_pass:
            best_pass = pass_at_1
            best_id = rid

    return best_id, best_pass


def main() -> None:
    """CLI 入口，输出最优 run。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="输出 JSON 而非 run_id")
    args = parser.parse_args()

    exp_dir = args.exp_dir.resolve()
    manifest = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    grid_ids = manifest.get("phases", {}).get("grid", {}).get("run_ids") or [
        r["run_id"] for r in manifest.get("runs", []) if r.get("phase") == "grid"
    ]

    best_id, best_pass = pick_best(grid_ids, exp_dir / "state" / "runs")

    if args.json:
        print(json.dumps({"best_run_id": best_id, "pass_at_1": best_pass}, ensure_ascii=False))
    else:
        if best_id:
            print(best_id)
        else:
            print("", end="")


if __name__ == "__main__":
    main()
