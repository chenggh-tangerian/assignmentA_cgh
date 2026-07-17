# sft_cgh2/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
代码修复式 SFT（错误代码 + 失败反馈 → 修复代码）。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `build_repair_sft.py` | 从 MBPP 失败 case 构修复数据 | `python sft_cgh2/scripts/build_repair_sft.py --cases sft/lora2_exp_cgh/outputs/r8_tqv_q4/eval/mbpp_cases.jsonl --output-dir sft_cgh2/data` |
| `auto_train_when_gpu_free.sh` | GPU 空闲时自动开训 | `bash sft_cgh2/scripts/auto_train_when_gpu_free.sh` |
| `serve.sh` | 启动修复 Demo（前端+/repair） | `bash sft_cgh2/scripts/serve.sh` |
| `serve_repair.py` | Demo 服务实现（被 serve.sh 调用） | `PORT=8081 python sft_cgh2/scripts/serve_repair.py` |

训练（配置在 `configs/`）：
```bash
/opt/conda/envs/chenggh-sft/bin/python -m llamafactory.cli train sft_cgh2/configs/qwen15_repair_lora_train.yaml
```
