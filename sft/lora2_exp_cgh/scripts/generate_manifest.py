#!/usr/bin/env python3
"""
功能: 生成 LoRA 网格实验的 manifest.json 与各 run 的 train/predict yaml。

输入: 实验目录、rank/target/quant 网格定义
输出: manifest.json、configs/*_train.yaml、*_predict.yaml、初始 state
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Phase1 主网格：rank × target × quantization
RANKS = [8, 16]
TARGETS = {
    "qv": "q_proj,v_proj",
    "all": "all",
}
QUANT_BITS = [None, 4]

EXP_NAME = "lora2_exp_cgh"
DEFAULT_LR = 1.0e-4
DEFAULT_EPOCHS = 3.0
DEFAULT_DROPOUT = 0.05


def alpha_for_rank(rank: int, multiplier: int = 2) -> int:
    """按 rank 与倍率计算 lora_alpha。"""
    return rank * multiplier


def run_id(rank: int, target_key: str, quant_bit: int | None) -> str:
    """由 rank/target/quant 拼出 run_id。"""
    q = "none" if quant_bit is None else str(quant_bit)
    return f"r{rank}_t{target_key}_q{q}"


def build_train_config(
    *,
    base_model: str,
    dataset_dir: str,
    output_dir: str,
    rank: int,
    target: str,
    quant_bit: int | None,
    lora_alpha: int,
    lora_dropout: float,
    learning_rate: float,
    num_train_epochs: float,
) -> dict:
    """构造单次训练 yaml 内容字典。"""
    cfg = {
        "model_name_or_path": base_model,
        "trust_remote_code": True,
        "stage": "sft",
        "do_train": True,
        "finetuning_type": "lora",
        "lora_rank": rank,
        "lora_alpha": lora_alpha,
        "lora_dropout": lora_dropout,
        "lora_target": target,
        "compute_accuracy": True,
        "dataset_dir": dataset_dir,
        "dataset": "code_sft_train",
        "eval_dataset": "code_sft_valid",
        "template": "qwen",
        "cutoff_len": 2048,
        "overwrite_cache": True,
        "preprocessing_num_workers": 8,
        "dataloader_num_workers": 8,
        "output_dir": output_dir,
        "logging_steps": 5,
        "save_steps": 1000,
        "save_total_limit": 1,
        "plot_loss": True,
        "overwrite_output_dir": True,
        "save_only_model": False,
        "report_to": "none",
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "learning_rate": learning_rate,
        "num_train_epochs": num_train_epochs,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.03,
        "max_grad_norm": 1.0,
        "gradient_checkpointing": True,
        "fp16": True,
        "bf16": False,
        "ddp_timeout": 180000000,
        "resume_from_checkpoint": None,
        "per_device_eval_batch_size": 2,
        "eval_strategy": "steps",
        "eval_steps": 1000,
    }
    # QLoRA：4-bit NF4 量化
    if quant_bit is not None:
        cfg["quantization_bit"] = quant_bit
        cfg["quantization_method"] = "bnb"
    return cfg


def build_predict_config(
    *,
    base_model: str,
    adapter_path: str,
    dataset_dir: str,
    output_dir: str,
    quant_bit: int | None,
) -> dict:
    """构造单次预测 yaml 内容字典。"""
    cfg = {
        "model_name_or_path": base_model,
        "adapter_name_or_path": adapter_path,
        "trust_remote_code": True,
        "stage": "sft",
        "do_predict": True,
        "finetuning_type": "lora",
        "dataset_dir": dataset_dir,
        "eval_dataset": "mbpp_sanitized_test",
        "template": "qwen",
        "cutoff_len": 2048,
        "overwrite_cache": True,
        "preprocessing_num_workers": 8,
        "dataloader_num_workers": 2,
        "output_dir": output_dir,
        "overwrite_output_dir": True,
        "report_to": "none",
        "per_device_eval_batch_size": 2,
        "predict_with_generate": True,
        "max_new_tokens": 768,
        "do_sample": False,
        "num_beams": 1,
        "fp16": True,
        "ddp_timeout": 180000000,
    }
    if quant_bit is not None:
        cfg["quantization_bit"] = quant_bit
        cfg["quantization_method"] = "bnb"
    return cfg


def initial_run_state(run: dict) -> dict:
    """生成单个 run 的初始状态字典。"""
    return {
        "run_id": run["run_id"],
        "phase": run.get("phase", "grid"),
        "params": run["params"],
        "paths": run["paths"],
        "stages": {
            "train": {"status": "pending", "started_at": None, "finished_at": None, "error": None},
            "predict": {"status": "pending", "started_at": None, "finished_at": None, "error": None},
            "eval": {"status": "pending", "started_at": None, "finished_at": None, "error": None},
        },
        "resources": {},
        "metrics": {},
        "overall_status": "pending",
    }


def exp_paths(exp_dir: Path, run_id_str: str) -> dict[str, str]:
    """返回某 run 相关路径字典。"""
    prefix = f"./sft/{EXP_NAME}"
    return {
        "train_config": f"{prefix}/configs/{run_id_str}_train.yaml",
        "predict_config": f"{prefix}/configs/{run_id_str}_predict.yaml",
        "model_dir": f"{prefix}/outputs/{run_id_str}/model",
        "predict_dir": f"{prefix}/outputs/{run_id_str}/predict",
        "eval_dir": f"{prefix}/outputs/{run_id_str}/eval",
        "log_dir": f"{prefix}/logs/{run_id_str}",
    }


def main() -> None:
    """写出全部配置、manifest 与状态文件。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp-dir", type=Path, required=True)
    parser.add_argument("--base-model", default="./Qwen1.5-0.5B-Chat")
    parser.add_argument("--dataset-dir", default="./sft/lora2_exp_cgh/data")
    parser.add_argument("--lora-dropout", type=float, default=DEFAULT_DROPOUT)
    parser.add_argument("--learning-rate", type=float, default=DEFAULT_LR)
    parser.add_argument("--num-train-epochs", type=float, default=DEFAULT_EPOCHS)
    parser.add_argument("--force", action="store_true", help="强制重新生成 manifest 和配置")
    args = parser.parse_args()

    exp_dir = args.exp_dir.resolve()
    project_root = exp_dir.parent.parent
    configs_dir = exp_dir / "configs"
    state_dir = exp_dir / "state" / "runs"
    manifest_path = exp_dir / "manifest.json"

    configs_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    if manifest_path.exists() and not args.force:
        print(f"Manifest 已存在: {manifest_path}（使用 --force 强制重新生成）")
        return

    runs = []
    for rank in RANKS:
        for target_key, target_val in TARGETS.items():
            for quant_bit in QUANT_BITS:
                rid = run_id(rank, target_key, quant_bit)
                paths = exp_paths(exp_dir, rid)
                alpha = alpha_for_rank(rank, 2)

                train_cfg = build_train_config(
                    base_model=args.base_model,
                    dataset_dir=args.dataset_dir,
                    output_dir=paths["model_dir"],
                    rank=rank,
                    target=target_val,
                    quant_bit=quant_bit,
                    lora_alpha=alpha,
                    lora_dropout=args.lora_dropout,
                    learning_rate=args.learning_rate,
                    num_train_epochs=args.num_train_epochs,
                )
                predict_cfg = build_predict_config(
                    base_model=args.base_model,
                    adapter_path=paths["model_dir"],
                    dataset_dir=args.dataset_dir,
                    output_dir=paths["predict_dir"],
                    quant_bit=quant_bit,
                )

                train_cfg_path = configs_dir / f"{rid}_train.yaml"
                predict_cfg_path = configs_dir / f"{rid}_predict.yaml"
                train_cfg_path.write_text(
                    yaml.safe_dump(train_cfg, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                predict_cfg_path.write_text(
                    yaml.safe_dump(predict_cfg, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )

                run = {
                    "run_id": rid,
                    "phase": "grid",
                    "params": {
                        "lora_rank": rank,
                        "lora_alpha": alpha,
                        "lora_dropout": args.lora_dropout,
                        "lora_target": target_val,
                        "lora_target_key": target_key,
                        "quantization_bit": quant_bit,
                        "learning_rate": args.learning_rate,
                        "num_train_epochs": args.num_train_epochs,
                        "finetuning_type": "lora" if quant_bit is None else "qlora",
                    },
                    "paths": paths,
                }
                runs.append(run)

                state_path = state_dir / f"{rid}.json"
                if not state_path.exists() or args.force:
                    state_path.write_text(
                        json.dumps(initial_run_state(run), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )

    # 保留 sweep 阶段 run（若已生成）
    existing_manifest = load_json_safe(manifest_path)
    sweep_runs = existing_manifest.get("sweep_runs", []) if existing_manifest else []

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "lora2_qlora_sft_hyperparam",
        "base_model": args.base_model,
        "dataset_dir": args.dataset_dir,
        "phases": {
            "grid": {
                "description": "Phase1 主网格：rank × target × quantization，alpha=2×rank，epoch=3",
                "run_ids": [r["run_id"] for r in runs],
            },
            "alpha_sweep": {
                "description": "Phase2：在 Phase1 最优配置上 sweep alpha {rank, 2×rank, 4×rank}",
                "run_ids": [r["run_id"] for r in sweep_runs if r.get("phase") == "alpha_sweep"],
            },
            "epoch_sweep": {
                "description": "Phase3：在 Phase1 最优配置上 sweep epoch {1, 5}",
                "run_ids": [r["run_id"] for r in sweep_runs if r.get("phase") == "epoch_sweep"],
            },
        },
        "matrix": {
            "lora_ranks": RANKS,
            "lora_targets": list(TARGETS.keys()),
            "quantization_bits": ["none", 4],
            "lora_alpha_rule": "2 * lora_rank",
            "lora_dropout": args.lora_dropout,
            "learning_rate": args.learning_rate,
            "num_train_epochs": args.num_train_epochs,
        },
        "total_runs": len(runs) + len(sweep_runs),
        "runs": runs,
        "sweep_runs": sweep_runs,
        "best_run_id": existing_manifest.get("best_run_id") if existing_manifest else None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"已生成 Phase1 {len(runs)} 组 -> {manifest_path}")


def load_json_safe(path: Path) -> dict | None:
    """安全读取 JSON，失败返回 None。"""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
