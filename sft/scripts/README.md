# sft/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`

| 脚本 | 功能 | 运行 |
|------|------|------|
| `run_all.sh` | 数据→训练→预测→评测全流程 | `bash sft/scripts/run_all.sh` |
| `prepare_data.sh` | 准备 Alpaca 训练/验证/测试数据 | `bash sft/scripts/prepare_data.sh` |
| `prepare_code_sft_data.py` | parquet→Alpaca JSON（被 prepare_data 调用） | `python sft/scripts/prepare_code_sft_data.py` |
| `prepare_mbpp_sanitized_data.py` | 准备 MBPP sanitized 评测集 | `python sft/scripts/prepare_mbpp_sanitized_data.py` |
| `train.sh` | Full SFT 训练 | `GPU_ID=0 bash sft/scripts/train.sh` |
| `predict_full.sh` | 测试集批量生成 | `MODEL_PATH=sft/outputs/qwen15_code_full_sft bash sft/scripts/predict_full.sh` |
| `evaluate_full.sh` | MBPP 执行评测 | `bash sft/scripts/evaluate_full.sh` |
| `evaluate_code_predictions.py` | 对 predictions 做 pass@1 评测 | `python sft/scripts/evaluate_code_predictions.py --help` |
| `infer_full.sh` / `infer.py` | 单条推理 | `bash sft/scripts/infer_full.sh --prompt "写一个回文判断函数"` |
| `run_base_predict_eval.sh` | 未微调基座模型对照评测 | `GPU_ID=0 bash sft/scripts/run_base_predict_eval.sh` |
