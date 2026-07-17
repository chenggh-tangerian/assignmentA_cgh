#!/usr/bin/env python3
"""
功能: 汇总各 run 状态与指标，生成中文实验报告 Markdown。

输入: state 目录、manifest
输出: reports/ 下实验报告 md
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHASE_ZH = {
    "grid": "Phase1 主网格",
    "alpha_sweep": "Phase2 Alpha Sweep",
    "epoch_sweep": "Phase3 Epoch Sweep",
}

METRIC_ZH = {
    "pass_at_1": "pass@1（任务通过率）",
    "syntax_pass_rate": "语法通过率",
    "avg_test_pass_rate": "测试用例通过率",
    "passed_tasks": "通过任务数",
    "total_tests": "测试用例总数",
    "passed_tests": "通过用例数",
    "num_tasks": "任务总数",
}

RESOURCE_ZH = {
    "trainable_params": "可训练参数量",
    "all_params": "总参数量",
    "trainable_pct": "可训练参数占比(%)",
    "adapter_size_mb": "Adapter 体积(MB)",
    "gpu_memory_peak_mib": "训练峰值显存(MiB)",
    "gpu_memory_avg_mib": "训练平均显存(MiB)",
    "train_runtime_sec": "训练耗时(秒)",
    "train_samples_per_second": "训练样本/秒",
    "train_steps_per_second": "训练步/秒",
    "train_loss": "训练损失",
    "eval_loss": "验证损失",
    "eval_accuracy": "验证准确率",
    "epoch": "训练轮数",
    "resume_checkpoint": "续训 checkpoint",
    "hyperparams": "超参快照",
}


def load_json(path: Path) -> dict[str, Any] | None:
    """读取 JSON，不存在返回 None。"""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_pct(v: float | None) -> str:
    """格式化百分比。"""
    if v is None:
        return "—"
    return f"{100 * v:.2f}%"


def fmt_num(v: Any, digits: int = 2) -> str:
    """格式化数值。"""
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def stage_zh(status: str) -> str:
    """阶段状态英文转中文。"""
    return {
        "done": "完成",
        "failed": "失败",
        "running": "进行中",
        "pending": "待运行",
        "skipped": "跳过",
    }.get(status, status)


def overall_zh(status: str) -> str:
    """总体状态英文转中文。"""
    return {
        "done": "全部完成",
        "failed": "有失败",
        "in_progress": "进行中",
        "pending": "未开始",
    }.get(status, status)


def target_zh(key: str) -> str:
    """LoRA target 键转中文说明。"""
    return {"qv": "q/v投影", "all": "全部层"}.get(key, key)


def quant_zh(q: Any) -> str:
    """量化设置转中文说明。"""
    if q is None:
        return "无(LoRA)"
    return f"{q}bit(QLoRA)"


def load_all_runs(state_dir: Path) -> list[dict[str, Any]]:
    """加载全部 run 状态。"""
    runs = []
    for path in sorted(state_dir.glob("*.json")):
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    return runs


def build_report(
    *,
    exp_dir: Path,
    baseline_metrics_path: Path,
    baseline_train_path: Path,
) -> tuple[dict[str, Any], str]:
    """构建完整报告 Markdown 文本。"""
    manifest = load_json(exp_dir / "manifest.json") or {}
    runs = load_all_runs(exp_dir / "state" / "runs")
    baseline_metrics = load_json(baseline_metrics_path)
    baseline_train = load_json(baseline_train_path)

    done = sum(1 for r in runs if r.get("overall_status") == "done")
    failed = sum(1 for r in runs if r.get("overall_status") == "failed")
    pending = len(runs) - done - failed

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "summary": {
            "total_runs": len(runs),
            "done": done,
            "failed": failed,
            "pending_or_in_progress": pending,
        },
        "phases": manifest.get("phases", {}),
        "best_run_id": manifest.get("best_run_id"),
        "matrix": manifest.get("matrix", {}),
        "baseline": {
            "metrics_path": str(baseline_metrics_path),
            "train_results_path": str(baseline_train_path),
            "mbpp_metrics": baseline_metrics,
            "train_results": baseline_train,
        },
        "runs": runs,
    }

    now = report["generated_at"]
    lines = [
        "# LoRA2 / QLoRA SFT 超参数实验报告",
        "",
        f"生成时间：{now}",
        "",
        "## 总览",
        "",
        f"- 实验组数：**{len(runs)}**",
        f"- 已完成：**{done}**",
        f"- 失败：**{failed}**",
        f"- 待运行/进行中：**{pending}**",
    ]

    if manifest.get("best_run_id"):
        lines.append(f"- Phase1 最优配置：**`{manifest['best_run_id']}`**")
    lines.append("")

    lines.extend(["## Baseline 对照（全量 SFT，不重新训练）", ""])
    if baseline_metrics:
        lines.extend(
            [
                f"- pass@1：**{fmt_pct(baseline_metrics.get('pass_at_1'))}**",
                f"- 语法通过率：**{fmt_pct(baseline_metrics.get('syntax_pass_rate'))}**",
                f"- 数据来源：`{baseline_metrics_path}`",
                "",
            ]
        )
    else:
        lines.append(f"- 未找到 baseline：`{baseline_metrics_path}`")
        lines.append("")

    if baseline_train:
        rt = baseline_train.get("train_runtime_sec") or baseline_train.get("train_runtime")
        lines.extend(
            [
                "### Baseline 训练速度",
                "",
                f"- 训练耗时：**{fmt_num(rt)}** 秒",
                f"- 步/秒：**{fmt_num(baseline_train.get('train_steps_per_second'))}**",
                "",
            ]
        )

    baseline_pass = baseline_metrics.get("pass_at_1") if baseline_metrics else None

    def append_table(run_list: list[dict[str, Any]], title: str) -> None:
        if not run_list:
            return
        lines.extend([f"## {title}", ""])
        lines.extend(
            [
                "| 实验ID | 类型 | rank | alpha | dropout | target | quant | lr | epoch | pass@1 | 峰值显存MiB | 步/秒 | 可训练参数 | 训练损失 | 状态 |",
                "|--------|------|------|-------|---------|--------|-------|-----|-------|--------|-------------|-------|------------|----------|------|",
            ]
        )
        for run in run_list:
            params = run.get("params", {})
            resources = run.get("resources", {})
            metrics = run.get("metrics", {})
            pass_at_1 = metrics.get("pass_at_1")
            alias = run.get("alias_of")
            status = overall_zh(run.get("overall_status", "?"))
            if alias:
                status = f"引用 `{alias}`"
            finetuning = params.get("finetuning_type", "lora")

            lines.append(
                "| {run_id} | {ft} | {rank} | {alpha} | {dropout} | {target} | {q} | {lr} | {epoch} | {pass_str} | {peak} | {sps} | {tp} | {loss} | {status} |".format(
                    run_id=run.get("run_id", "?"),
                    ft=finetuning,
                    rank=params.get("lora_rank", "?"),
                    alpha=params.get("lora_alpha", "?"),
                    dropout=params.get("lora_dropout", "?"),
                    target=target_zh(params.get("lora_target_key", "?")),
                    q=quant_zh(params.get("quantization_bit")),
                    lr=params.get("learning_rate", "?"),
                    epoch=params.get("num_train_epochs", "?"),
                    pass_str=fmt_pct(pass_at_1) if pass_at_1 is not None else "—",
                    peak=fmt_num(resources.get("gpu_memory_peak_mib"), 0),
                    sps=fmt_num(resources.get("train_steps_per_second")),
                    tp=fmt_num(resources.get("trainable_params"), 0),
                    loss=fmt_num(resources.get("train_loss")),
                    status=status,
                )
            )
        lines.append("")

    grid_runs = [r for r in runs if r.get("phase") == "grid"]
    alpha_runs = [r for r in runs if r.get("phase") == "alpha_sweep"]
    epoch_runs = [r for r in runs if r.get("phase") == "epoch_sweep"]

    append_table(grid_runs, "Phase1 主网格结果")
    append_table(alpha_runs, "Phase2 Alpha Sweep 结果")
    append_table(epoch_runs, "Phase3 Epoch Sweep 结果")

    # 作业要求字段对照表
    lines.extend(
        [
            "## 作业要求覆盖检查",
            "",
            "| 要求 | 配置/实验 | 记录位置 |",
            "|------|-----------|----------|",
            "| LoRA/QLoRA 微调 | `finetuning_type` + `quantization_bit` | `configs/*_train.yaml`, `state/runs/*.json` params |",
            "| lora_rank | Phase1 grid {8,16} | params + 报告 |",
            "| lora_alpha | Phase1: 2×rank；Phase2 sweep {1×,2×,4×}rank | params + 报告 |",
            "| lora_dropout | 固定 0.05 | params + 报告 |",
            "| lora_target | q_proj,v_proj / all | params + 报告 |",
            "| quantization_bit | none(LoRA) / 4(QLoRA) | params + 报告 |",
            "| learning_rate | 1e-4；Phase2/3 随最优配置 | params + 报告 |",
            "| epoch | Phase1: 3；Phase3 sweep {1,5} | params + 报告 |",
            "| 显存占用 | 峰值 MiB | `logs/<run>/gpu_memory.csv` → resources |",
            "| 训练速度 | steps/sec, samples/sec | `train_results.json` → resources |",
            "| 参数量 | trainable/all params | 训练日志 → resources |",
            "| 最终测试结果 | MBPP pass@1 等 | `outputs/<run>/eval/mbpp_metrics.json` → metrics |",
            "",
        ]
    )

    lines.extend(["## 各组详情", ""])
    for run in runs:
        rid = run.get("run_id", "?")
        lines.append(f"### `{rid}`")
        lines.append("")
        params = run.get("params", {})
        lines.append(
            f"- 阶段：**{PHASE_ZH.get(run.get('phase', ''), run.get('phase', '?'))}** | "
            f"状态：**{overall_zh(run.get('overall_status', '?'))}**"
        )
        if run.get("alias_of"):
            lines.append(f"- 引用已有 run：`{run['alias_of']}`（跳过重复训练）")
        if run.get("base_run_id"):
            lines.append(f"- 基于 Phase1 最优：`{run['base_run_id']}`")
        lines.append(
            f"- 超参：rank={params.get('lora_rank')}, alpha={params.get('lora_alpha')}, "
            f"dropout={params.get('lora_dropout')}, target={params.get('lora_target')}, "
            f"quant={quant_zh(params.get('quantization_bit'))}, lr={params.get('learning_rate')}, "
            f"epoch={params.get('num_train_epochs')}"
        )
        resources = run.get("resources", {})
        if resources:
            lines.append("- 资源：")
            for k, v in sorted(resources.items()):
                lines.append(f"  - {RESOURCE_ZH.get(k, k)}：{v}")
        metrics = run.get("metrics", {})
        if metrics:
            lines.append("- 评测：")
            for k, v in sorted(metrics.items()):
                if k in ("pass_at_1", "syntax_pass_rate", "avg_test_pass_rate") and isinstance(v, float):
                    lines.append(f"  - {METRIC_ZH.get(k, k)}：{fmt_pct(v)}")
                else:
                    lines.append(f"  - {METRIC_ZH.get(k, k)}：{v}")
        lines.append("")

    lines.extend(
        [
            "## 断点续跑",
            "",
            "详见 `sft/lora2_exp_cgh/README.md`。",
            "",
        ]
    )

    return report, "\n".join(lines)


def main() -> None:
    """写出实验报告文件。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", type=Path, required=True)
    parser.add_argument(
        "--baseline-metrics",
        type=Path,
        default=Path("sft/outputs/eval_mbpp/mbpp_metrics.json"),
    )
    parser.add_argument(
        "--baseline-train",
        type=Path,
        default=Path("sft/outputs/qwen15_code_full_sft/train_results.json"),
    )
    args = parser.parse_args()

    exp_dir = args.exp_dir.resolve()
    project_root = exp_dir.parent.parent
    baseline_metrics = (project_root / args.baseline_metrics).resolve()
    baseline_train = (project_root / args.baseline_train).resolve()

    report, md = build_report(
        exp_dir=exp_dir,
        baseline_metrics_path=baseline_metrics,
        baseline_train_path=baseline_train,
    )

    reports_dir = exp_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "experiment_report.json"
    md_path = reports_dir / "experiment_report.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(md + "\n", encoding="utf-8")
    print(f"报告已生成：\n  {json_path}\n  {md_path}")


if __name__ == "__main__":
    main()
