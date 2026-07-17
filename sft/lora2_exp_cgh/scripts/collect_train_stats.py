#!/usr/bin/env python3
"""
功能: 从训练日志/GPU 监控汇总单次 LoRA run 的训练统计。

输入: run_id、manifest、train log、gpu csv、model 目录
输出: 该 run 的 train_stats.json（时长、loss、显存、adapter 大小等）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


TRAINABLE_RE = re.compile(
    r"trainable params:\s*([\d,]+)\s*\|\|\s*all params:\s*([\d,]+)\s*\|\|\s*trainable%:\s*([\d.]+)",
    re.IGNORECASE,
)


def parse_int(s: str) -> int:
    """从字符串解析整数，失败返回 0。"""
    return int(s.replace(",", ""))


def parse_train_log(log_path: Path) -> dict[str, Any]:
    """从训练日志文本提取关键统计。"""
    out: dict[str, Any] = {}
    if not log_path.exists():
        return out
    text = log_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = TRAINABLE_RE.search(line)
        if m:
            out["trainable_params"] = parse_int(m.group(1))
            out["all_params"] = parse_int(m.group(2))
            out["trainable_pct"] = float(m.group(3))
    return out


def parse_train_results(model_dir: Path) -> dict[str, Any]:
    """读取 model 目录下 train_results.json。"""
    out: dict[str, Any] = {}
    results_path = model_dir / "train_results.json"
    if not results_path.exists():
        return out
    data = json.loads(results_path.read_text(encoding="utf-8"))
    out["train_loss"] = data.get("train_loss")
    out["train_runtime_sec"] = data.get("train_runtime")
    out["train_samples_per_second"] = data.get("train_samples_per_second")
    out["train_steps_per_second"] = data.get("train_steps_per_second")
    out["epoch"] = data.get("epoch")
    return out


def parse_trainer_log_jsonl(model_dir: Path) -> dict[str, Any]:
    """从 trainer_log.jsonl 提取最后一次 eval 指标。"""
    out: dict[str, Any] = {}
    path = model_dir / "trainer_log.jsonl"
    if not path.exists():
        return out
    last_eval: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "eval_loss" in row:
            last_eval = row
    if last_eval:
        out["eval_loss"] = last_eval.get("eval_loss")
        out["eval_accuracy"] = last_eval.get("eval_accuracy")
    return out


def parse_gpu_csv(csv_path: Path) -> dict[str, Any]:
    """解析 GPU 监控 CSV，统计峰值显存等。"""
    out: dict[str, Any] = {}
    if not csv_path.exists():
        return out

    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    gpu_total = None
    for row in rows:
        total = row.get("memory_total_MiB", "NA")
        if total not in ("", "NA"):
            try:
                gpu_total = int(float(total))
                break
            except ValueError:
                pass

    peak_used = 0
    peak_util = 0
    samples = 0
    total_used = 0.0

    for row in rows:
        used = row.get("memory_used_MiB", "NA")
        if used in ("", "NA"):
            continue
        try:
            used_i = int(float(used))
        except ValueError:
            continue
        if used_i > 100000:
            continue
        if gpu_total is not None and used_i > gpu_total * 1.05:
            continue
        samples += 1
        total_used += used_i
        peak_used = max(peak_used, used_i)
        util = row.get("gpu_util_pct", "NA")
        if util not in ("", "NA"):
            try:
                peak_util = max(peak_util, int(float(util)))
            except ValueError:
                pass

    if samples:
        out["gpu_memory_peak_mib"] = peak_used
        out["gpu_memory_avg_mib"] = round(total_used / samples, 2)
        out["gpu_util_peak_pct"] = peak_util
        out["gpu_monitor_samples"] = samples
    if gpu_total is not None:
        out["gpu_memory_total_mib"] = gpu_total
    return out


def adapter_size_bytes(model_dir: Path) -> int | None:
    """统计 adapter 权重文件总字节数。"""
    # 优先统计 model 根目录 adapter，避免把 checkpoint 副本重复计入
    for name in ("adapter_model.safetensors", "adapter_model.bin"):
        p = model_dir / name
        if p.exists():
            return p.stat().st_size
    candidates = list(model_dir.glob("checkpoint-*/adapter_model*.safetensors")) + list(
        model_dir.glob("checkpoint-*/adapter_model.bin")
    )
    if not candidates:
        return None
    return max(p.stat().st_size for p in candidates)


def load_run_params(manifest_path: Path, run_id: str) -> dict[str, Any]:
    """从 manifest 读取指定 run 的超参。"""
    if not manifest_path.exists() or not run_id:
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for run in manifest.get("runs", []) + manifest.get("sweep_runs", []):
        if run.get("run_id") == run_id:
            return dict(run.get("params", {}))
    return {}


def main() -> None:
    """汇总各来源统计并写出 train_stats.json。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-log", type=Path, required=True)
    parser.add_argument("--gpu-csv", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--resume-checkpoint", default="")
    args = parser.parse_args()

    summary: dict[str, Any] = {}
    summary.update(parse_train_log(args.train_log))
    summary.update(parse_train_results(args.model_dir))
    summary.update(parse_trainer_log_jsonl(args.model_dir))
    summary.update(parse_gpu_csv(args.gpu_csv))

    size = adapter_size_bytes(args.model_dir)
    if size is not None:
        summary["adapter_size_bytes"] = size
        summary["adapter_size_mb"] = round(size / (1024 * 1024), 4)

    if args.manifest and args.run_id:
        params = load_run_params(args.manifest, args.run_id)
        summary["hyperparams"] = params

    if args.resume_checkpoint:
        summary["resume_checkpoint"] = args.resume_checkpoint

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote resource summary -> {args.output}")


if __name__ == "__main__":
    main()
