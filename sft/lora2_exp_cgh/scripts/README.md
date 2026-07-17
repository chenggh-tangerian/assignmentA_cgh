# sft/lora2_exp_cgh/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
LoRA / QLoRA 超参扫参（rank×target×量化→alpha→epoch）。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `run_all.sh` | 初始化→全部训练评测→报告 | `GPU_ID=0 bash sft/lora2_exp_cgh/scripts/run_all.sh` |
| `00_init.sh` | 准备 data + 生成 Phase1 配置 | `bash sft/lora2_exp_cgh/scripts/00_init.sh --force` |
| `01_train_run.sh` | 训练单组 | `GPU_ID=0 bash sft/lora2_exp_cgh/scripts/01_train_run.sh r8_tqv_q4` |
| `02_predict_eval_run.sh` | 预测 + MBPP 评测 | `GPU_ID=0 bash sft/lora2_exp_cgh/scripts/02_predict_eval_run.sh r8_tqv_q4` |
| `03_report.sh` | 汇总报告 | `bash sft/lora2_exp_cgh/scripts/03_report.sh` |
| `monitor_gpu.sh` | 采显存（验收用） | `bash sft/lora2_exp_cgh/scripts/monitor_gpu.sh` |
| `setup_data.py` | 软链/准备实验数据 | `python sft/lora2_exp_cgh/scripts/setup_data.py` |
| `generate_manifest.py` | 生成实验清单 | `python sft/lora2_exp_cgh/scripts/generate_manifest.py` |
| `generate_sweep_runs.py` | 生成扫参 run 配置 | `python sft/lora2_exp_cgh/scripts/generate_sweep_runs.py` |
| `pick_best_run.py` | 选最优 run | `python sft/lora2_exp_cgh/scripts/pick_best_run.py` |
| `update_state.py` | 更新 run 状态 | `python sft/lora2_exp_cgh/scripts/update_state.py` |
| `collect_train_stats.py` | 收集训练统计 | `python sft/lora2_exp_cgh/scripts/collect_train_stats.py` |
| `prune_checkpoints.py` | 清理多余 checkpoint | `python sft/lora2_exp_cgh/scripts/prune_checkpoints.py` |
| `generate_report.py` / `gen_results_html.py` | 生成 md/html 报告 | `python sft/lora2_exp_cgh/scripts/generate_report.py` |
| `common.sh` | 公共环境变量（被其它 sh source） | — |
