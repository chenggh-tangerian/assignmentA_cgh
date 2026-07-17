# sft/scripts_cgh

根目录执行：`cd /root/siton-tmp/assignment_A`  
产出写入 `sft/data_cgh/`、`sft/outputs_cgh/`（不改 baseline）。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `run_analysis.sh` | 错误分析 baseline 评测结果 | `bash sft/scripts_cgh/run_analysis.sh` |
| `analyze_errors.py` | 错误分析核心 | `python sft/scripts_cgh/analyze_errors.py --help` |
| `prepare_signature_data.sh` | 准备带函数签名的数据 | `bash sft/scripts_cgh/prepare_signature_data.sh` |
| `prepare_mbpp_with_signature.py` | MBPP 评测集加签名 | `python sft/scripts_cgh/prepare_mbpp_with_signature.py` |
| `prepare_sft_train_with_signature.py` | 训练集加签名 | `python sft/scripts_cgh/prepare_sft_train_with_signature.py` |
| `run_signature_experiment.sh` | 仅推理加签名实验 | `GPU_ID=0 bash sft/scripts_cgh/run_signature_experiment.sh` |
| `predict_with_signature.sh` | 签名 prompt 预测 | `GPU_ID=0 bash sft/scripts_cgh/predict_with_signature.sh` |
| `run_sft_signature_full.sh` | 签名数据重训+评测全流程 | `GPU_ID=0 bash sft/scripts_cgh/run_sft_signature_full.sh` |
| `run_train_new_sft.sh` / `train_with_signature.sh` | 签名数据训练 | `GPU_ID=0 bash sft/scripts_cgh/run_train_new_sft.sh` |
| `run_eval_sft_with_signature.sh` | 签名版模型评测 | `GPU_ID=0 bash sft/scripts_cgh/run_eval_sft_with_signature.sh` |
| `run_fair_compare_eval.sh` | 无签名公平对比评测 | `GPU_ID=0 bash sft/scripts_cgh/run_fair_compare_eval.sh` |
| `export_mbpp_failures_for_sft.py` | 导出失败样本 | `python sft/scripts_cgh/export_mbpp_failures_for_sft.py` |
| `signature_utils.py` | 签名工具库（被其它脚本 import） | — |
