# sft_cgh_dataop3/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
公平数据优化（~60% 全量，禁止测试集泄漏）。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `build_data.sh` | 软过滤 + 签名注入建数据 | `bash sft_cgh_dataop3/scripts/build_data.sh` |
| `build_data.py` | 建数据核心 | `python sft_cgh_dataop3/scripts/build_data.py` |
| `filter_high_quality.py` | 软过滤工具 | `python sft_cgh_dataop3/scripts/filter_high_quality.py` |
| `train.sh` | Full SFT | `GPU_ID=0 bash sft_cgh_dataop3/scripts/train.sh` |
| `train_ep2500.sh` | 加长训练（2500 steps） | `GPU_ID=0 bash sft_cgh_dataop3/scripts/train_ep2500.sh` |
| `train_ckptsave.sh` | 训练并多存 checkpoint | `GPU_ID=0 bash sft_cgh_dataop3/scripts/train_ckptsave.sh` |
| `predict.sh` | 预测 + 评测 | `GPU_ID=0 bash sft_cgh_dataop3/scripts/predict.sh` |
| `eval.sh` | DPO 协议 MBPP 评测 | `GPU_ID=0 bash sft_cgh_dataop3/scripts/eval.sh` |
| `compare_report.sh` | 与 baseline 对比报告 | `bash sft_cgh_dataop3/scripts/compare_report.sh` |
