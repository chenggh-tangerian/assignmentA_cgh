# sft_cgh_dataop3

公平版：只用 `sft/data`，规模约全量 **60%**，按错误类型轻度加码。**禁止测试集进训练。**

详见 [DATA_PLAN.md](./DATA_PLAN.md)。

```bash
bash sft_cgh_dataop3/scripts/build_data.sh
GPU_ID=0 nohup bash sft_cgh_dataop3/scripts/train.sh \
  > sft_cgh_dataop3/outputs/nohup_train.log 2>&1 &
GPU_ID=0 bash sft_cgh_dataop3/scripts/predict.sh
```
