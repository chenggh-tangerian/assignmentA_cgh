# sft_cgh_dataop/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
高质量少样本筛选 + Full SFT（产出仅在本模块目录）。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `run_all.sh` | 筛选→训练→预测评测 | `GPU_ID=0 bash sft_cgh_dataop/scripts/run_all.sh` |
| `run_filter.sh` | 五维筛选高质量数据 | `bash sft_cgh_dataop/scripts/run_filter.sh` |
| `filter_high_quality.py` | 筛选核心 | `python sft_cgh_dataop/scripts/filter_high_quality.py` |
| `train.sh` | HQ Full SFT（默认 ep3） | `GPU_ID=0 bash sft_cgh_dataop/scripts/train.sh` |
| `predict.sh` | 签名版 MBPP 评测 | `GPU_ID=0 bash sft_cgh_dataop/scripts/predict.sh` |
| `train_continue_ep6.sh` | 从 ep3 继续训到 ep6 | `GPU_ID=0 bash sft_cgh_dataop/scripts/train_continue_ep6.sh` |
| `predict_ep6.sh` | ep6 模型评测（写 outputs_2） | `GPU_ID=0 bash sft_cgh_dataop/scripts/predict_ep6.sh` |

可选：`SKIP_TRAIN=1 bash sft_cgh_dataop/scripts/run_all.sh`；`TARGET_TRAIN_SIZE=4000 bash .../run_filter.sh`
