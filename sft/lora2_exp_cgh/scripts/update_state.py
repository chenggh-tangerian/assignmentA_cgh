#!/usr/bin/env python3
"""
功能: 更新单个 LoRA run 的状态 JSON（阶段、时间、overall）。

输入: state 文件路径、要更新的字段
输出: 写回更新后的 state JSON
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    """返回 UTC 时间字符串。"""
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    """读取 state JSON。"""
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    """保存 state JSON。"""
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def recompute_overall(state: dict[str, Any]) -> None:
    """根据各阶段状态重算 overall。"""
    stages = state.get("stages", {})
    statuses = [stages.get(k, {}).get("status", "pending") for k in ("train", "predict", "eval")]
    if state.get("alias_of"):
        ref = state.get("alias_status", "pending")
        state["overall_status"] = ref
    elif any(s == "failed" for s in statuses):
        state["overall_status"] = "failed"
    elif all(s == "done" for s in statuses):
        state["overall_status"] = "done"
    elif any(s in ("running", "done") for s in statuses):
        state["overall_status"] = "in_progress"
    else:
        state["overall_status"] = "pending"
    state["updated_at"] = utc_now()


def main() -> None:
    """CLI 更新指定字段并写回。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--stage", choices=["train", "predict", "eval"], required=True)
    parser.add_argument("--status", choices=["pending", "running", "done", "failed", "skipped"], required=True)
    parser.add_argument("--error", default="")
    parser.add_argument("--set-resources", type=Path, help="JSON file to merge into resources")
    parser.add_argument("--set-metrics", type=Path, help="JSON file to merge into metrics")
    args = parser.parse_args()

    state = load_state(args.state_file)
    stage = state.setdefault("stages", {}).setdefault(args.stage, {})

    if args.status == "running":
        stage["started_at"] = stage.get("started_at") or utc_now()
        stage["error"] = None
    elif args.status in ("done", "failed", "skipped"):
        stage["finished_at"] = utc_now()
        if args.error:
            stage["error"] = args.error
        elif args.status == "done":
            stage["error"] = None

    stage["status"] = args.status

    if args.set_resources and args.set_resources.exists():
        resources = json.loads(args.set_resources.read_text(encoding="utf-8"))
        state.setdefault("resources", {}).update(resources)

    if args.set_metrics and args.set_metrics.exists():
        metrics = json.loads(args.set_metrics.read_text(encoding="utf-8"))
        state.setdefault("metrics", {}).update(metrics)

    recompute_overall(state)
    save_state(args.state_file, state)
    print(f"Updated {args.state_file}: stage={args.stage} status={args.status} overall={state['overall_status']}")


if __name__ == "__main__":
    main()
