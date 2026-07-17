# LoRA2 / QLoRA 超参数实验（精简版）

用 baseline 同一套数据做 LoRA/QLoRA，记录显存、速度、参数量、MBPP pass@1，并生成报告。

## 实验设计

| 阶段 | 内容 |
|------|------|
| Phase1 | rank{8,16} × target{qv,all} × quant{none,4} → **8 组** |
| Phase2 | 最优配置上扫 alpha ∈ {1×,2×,4×}rank |
| Phase3 | 最优配置上扫 epoch ∈ {1,5} |

## 怎么跑

```bash
cd /root/siton-tmp/assignment_A

# 初始化（生成 yaml / manifest）
bash sft/lora2_exp_cgh/scripts/00_init.sh --force

# 一键跑完全部并出报告
GPU_ID=0 bash sft/lora2_exp_cgh/scripts/run_all.sh
```

或单组：

```bash
GPU_ID=0 bash sft/lora2_exp_cgh/scripts/01_train_run.sh r8_tqv_q4
GPU_ID=0 bash sft/lora2_exp_cgh/scripts/02_predict_eval_run.sh r8_tqv_q4
bash sft/lora2_exp_cgh/scripts/03_report.sh
```

## 脚本（仅保留这些）

| 脚本 | 作用 |
|------|------|
| `00_init.sh` | 准备 data + 生成 Phase1 配置 |
| `01_train_run.sh` | 训练一组 |
| `02_predict_eval_run.sh` | 预测 + MBPP 评测 |
| `03_report.sh` | 出报告 |
| `run_all.sh` | 上面全流程串起来 |
| `monitor_gpu.sh` | 采显存（验收指标） |

Python：`setup_data.py`、`generate_manifest.py`、`generate_sweep_runs.py`、`pick_best_run.py`、`update_state.py`、`collect_train_stats.py`、`prune_checkpoints.py`、`generate_report.py`、`gen_results_html.py`。

## 产出

- 报告：`reports/experiment_report.md`
- 可视化：`reports/lora2_acceptance_dashboard.html`
- 每组结果：`state/runs/<run_id>.json`、`outputs/<run_id>/`
