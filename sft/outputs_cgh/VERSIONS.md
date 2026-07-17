# SFT 模型版本对照

| 版本 | 路径 | 数据 | 说明 |
|------|------|------|------|
| **baseline（保留对比）** | `sft/outputs/qwen15_code_full_sft/` | `sft/data/code_sft_*` | 原始全量 SFT，勿覆盖 |
| **v2 新版（当前训练）** | `sft/outputs_cgh/qwen15_sft_with_signature/` | `sft/data_cgh/code_sft_*_with_signature` | 同 baseline 超参 + instruction 带函数签名 |

训练超参与 `sft/configs/qwen15_code_full_sft.yaml` 完全一致，仅数据集与输出目录不同。
