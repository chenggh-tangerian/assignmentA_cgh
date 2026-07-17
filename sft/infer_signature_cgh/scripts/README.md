# sft/infer_signature_cgh/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
只在推理 prompt 加函数签名，不改训练数据/权重。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `run_all.sh` | 造数据→推理→评测→错误分析 | `GPU_ID=0 bash sft/infer_signature_cgh/scripts/run_all.sh` |
| `predict.sh` | 签名版 MBPP 批量预测 | `GPU_ID=0 bash sft/infer_signature_cgh/scripts/predict.sh` |
