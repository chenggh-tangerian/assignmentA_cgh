#!/usr/bin/env python3
"""
功能: 在最优 run 附近生成 alpha/epoch 等 sweep 变体配置。

输入: manifest、最优 run_id、sweep 参数
输出: 新增 sweep run 的 yaml/state，并更新 manifest
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_manifest import (
    EXP_NAME,
    build_predict_config,
    build_train_config,
    initial_run_state,
    exp_paths,
)


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON。"""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    """写出 JSON。"""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_run(manifest: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    """在 manifest 中按 run_id 查找。"""
    for run in manifest.get("runs", []) + manifest.get("sweep_runs", []):
        if run["run_id"] == run_id:
            return run
    return None


def copy_metrics_from_alias(state_dir: Path, sweep_id: str, alias_id: str) -> None:
    """若 sweep run 与已有 run 参数完全相同，直接引用其结果。"""
    alias_state = load_json(state_dir / f"{alias_id}.json")
    sweep_state = load_json(state_dir / f"{sweep_id}.json")
    sweep_state["alias_of"] = alias_id
    sweep_state["alias_status"] = alias_state.get("overall_status", "done")
    sweep_state["resources"] = dict(alias_state.get("resources", {}))
    sweep_state["metrics"] = dict(alias_state.get("metrics", {}))
    for stage in ("train", "predict", "eval"):
        sweep_state.setdefault("stages", {})[stage] = {
            "status": "skipped",
            "started_at": None,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "note": f"与 {alias_id} 参数相同，跳过重复训练",
        }
    sweep_state["overall_status"] = alias_state.get("overall_status", "done")
    save_json(state_dir / f"{sweep_id}.json", sweep_state)


def create_sweep_run(
    *,
    exp_dir: Path,
    base_run: dict[str, Any],
    sweep_id: str,
    phase: str,
    overrides: dict[str, Any],
    base_model: str,
    dataset_dir: str,
    configs_dir: Path,
    state_dir: Path,
) -> dict[str, Any]:
    """创建单个 sweep run 配置与状态。"""
    params = dict(base_run["params"])
    params.update(overrides)
    paths = exp_paths(exp_dir, sweep_id)

    train_cfg = build_train_config(
        base_model=base_model,
        dataset_dir=dataset_dir,
        output_dir=paths["model_dir"],
        rank=params["lora_rank"],
        target=params["lora_target"],
        quant_bit=params.get("quantization_bit"),
        lora_alpha=params["lora_alpha"],
        lora_dropout=params["lora_dropout"],
        learning_rate=params["learning_rate"],
        num_train_epochs=params["num_train_epochs"],
    )
    predict_cfg = build_predict_config(
        base_model=base_model,
        adapter_path=paths["model_dir"],
        dataset_dir=dataset_dir,
        output_dir=paths["predict_dir"],
        quant_bit=params.get("quantization_bit"),
    )

    (configs_dir / f"{sweep_id}_train.yaml").write_text(
        yaml.safe_dump(train_cfg, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (configs_dir / f"{sweep_id}_predict.yaml").write_text(
        yaml.safe_dump(predict_cfg, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    run = {
        "run_id": sweep_id,
        "phase": phase,
        "base_run_id": base_run["run_id"],
        "params": params,
        "paths": paths,
    }

    state_path = state_dir / f"{sweep_id}.json"
    if not state_path.exists():
        save_json(state_path, initial_run_state(run))

    return run


def params_match(a: dict[str, Any], b: dict[str, Any], keys: list[str]) -> bool:
    """比较两组参数在指定键上是否一致。"""
    return all(a.get(k) == b.get(k) for k in keys)


def main() -> None:
    """批量生成 sweep runs。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", type=Path, required=True)
    parser.add_argument("--best-run-id", default="", help="Phase1 最优 run_id；留空则自动选取")
    parser.add_argument("--phase", choices=["alpha", "epoch", "both"], default="both")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    exp_dir = args.exp_dir.resolve()
    manifest_path = exp_dir / "manifest.json"
    manifest = load_json(manifest_path)
    state_dir = exp_dir / "state" / "runs"
    configs_dir = exp_dir / "configs"

    best_id = args.best_run_id
    if not best_id:
        from pick_best_run import pick_best

        grid_ids = manifest.get("phases", {}).get("grid", {}).get("run_ids", [])
        best_id, best_pass = pick_best(grid_ids, state_dir)
        if not best_id:
            raise SystemExit("Phase1 尚无已完成评测的 run，无法生成 sweep 配置")
        print(f"自动选取 Phase1 最优: {best_id} (pass@1={best_pass})")

    base_run = find_run(manifest, best_id)
    if not base_run:
        raise SystemExit(f"未在 manifest 中找到 run: {best_id}")

    base_params = base_run["params"]
    rank = base_params["lora_rank"]
    base_model = manifest.get("base_model", "./Qwen1.5-0.5B-Chat")
    dataset_dir = manifest.get("dataset_dir", "./sft/data")

    new_sweep_runs: list[dict[str, Any]] = []
    existing_sweeps = {r["run_id"]: r for r in manifest.get("sweep_runs", [])}

    compare_keys = [
        "lora_rank",
        "lora_alpha",
        "lora_dropout",
        "lora_target",
        "quantization_bit",
        "learning_rate",
        "num_train_epochs",
    ]

    if args.phase in ("alpha", "both"):
        alpha_values = [
            ("a1x", rank, 1),
            ("a2x", rank * 2, 2),
            ("a4x", rank * 4, 4),
        ]
        for suffix, alpha, mult in alpha_values:
            sweep_id = f"{best_id}_alpha_{suffix}"
            if sweep_id in existing_sweeps and not args.force:
                new_sweep_runs.append(existing_sweeps[sweep_id])
                continue

            overrides = {"lora_alpha": alpha, "alpha_multiplier": mult}
            run = create_sweep_run(
                exp_dir=exp_dir,
                base_run=base_run,
                sweep_id=sweep_id,
                phase="alpha_sweep",
                overrides=overrides,
                base_model=base_model,
                dataset_dir=dataset_dir,
                configs_dir=configs_dir,
                state_dir=state_dir,
            )
            new_sweep_runs.append(run)

            # 若与 Phase1 最优 run 参数完全一致，标记为 alias 跳过
            if params_match(run["params"], base_params, compare_keys):
                copy_metrics_from_alias(state_dir, sweep_id, best_id)
                print(f"  {sweep_id} 与 {best_id} 相同，标记 alias 跳过")

    if args.phase in ("epoch", "both"):
        for ep in (1, 5):
            sweep_id = f"{best_id}_epoch_{ep}"
            if sweep_id in existing_sweeps and not args.force:
                new_sweep_runs.append(existing_sweeps[sweep_id])
                continue

            overrides = {"num_train_epochs": float(ep)}
            run = create_sweep_run(
                exp_dir=exp_dir,
                base_run=base_run,
                sweep_id=sweep_id,
                phase="epoch_sweep",
                overrides=overrides,
                base_model=base_model,
                dataset_dir=dataset_dir,
                configs_dir=configs_dir,
                state_dir=state_dir,
            )
            new_sweep_runs.append(run)

            if params_match(run["params"], base_params, compare_keys):
                copy_metrics_from_alias(state_dir, sweep_id, best_id)
                print(f"  {sweep_id} 与 {best_id} 相同，标记 alias 跳过")

    # 合并 sweep runs：只保留当前 best_id 的 sweep，丢弃其他 base 的旧配置
    new_ids = {r["run_id"] for r in new_sweep_runs}
    kept = [
        r
        for r in manifest.get("sweep_runs", [])
        if r.get("base_run_id") == best_id and r["run_id"] not in new_ids
    ]
    kept.extend(new_sweep_runs)
    removed = [
        r["run_id"]
        for r in manifest.get("sweep_runs", [])
        if r.get("base_run_id") != best_id
    ]
    if removed:
        print(f"  移除旧 base 的 sweep: {', '.join(removed)}")

    manifest["sweep_runs"] = kept
    manifest["best_run_id"] = best_id
    manifest["phases"]["alpha_sweep"]["run_ids"] = [
        r["run_id"] for r in kept if r.get("phase") == "alpha_sweep"
    ]
    manifest["phases"]["epoch_sweep"]["run_ids"] = [
        r["run_id"] for r in kept if r.get("phase") == "epoch_sweep"
    ]
    manifest["total_runs"] = len(manifest.get("runs", [])) + len(kept)
    manifest["sweep_generated_at"] = datetime.now(timezone.utc).isoformat()

    save_json(manifest_path, manifest)
    print(f"已更新 manifest: best={best_id}, sweep_runs={len(kept)} -> {manifest_path}")


if __name__ == "__main__":
    main()
