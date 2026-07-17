# a5_cgh — A5 负责模块（Greedy / CoT / ToT）

本目录包含本人负责的 Test-Time 基线与 ToT 评测脚本，输出格式与 `eval_tot` 对齐（metrics + token_cost + timing）。

## 负责范围

| 策略 | 说明 | 脚本 |
|------|------|------|
| **Greedy** | MBPP 官方 Prompt，`temperature=0` 单次解码 | `scripts/eval_greedy.sh` |
| **CoT** | Reasoning / Key steps / Final code 结构化 Prompt，greedy 解码 | `scripts/eval_cot.sh` |
| **ToT** | Tree of Thoughts 两阶段 beam 搜索 | `scripts/eval_tot.sh` |

## 默认配置

- **评测集**：MBPP sanitized test（257 题）
- **默认模型**：`rl/outputs/train_lora_ppo_full/checkpoint-1304`（与 ToT 实验一致）
- **Greedy** `max_new_tokens=512`
- **CoT** `max_new_tokens=768`（CoT 输出更长）

## 运行前确认

```bash
cd /root/siton-tmp/assignment_A

# 1. Smoke test（2 题，约 1~2 分钟）
LIMIT=2 bash a5_cgh/scripts/eval_greedy.sh
LIMIT=2 bash a5_cgh/scripts/eval_cot.sh

# 2. 全量（257 题，Greedy ~30min，CoT ~40min，视 GPU 而定）
bash a5_cgh/scripts/eval_greedy.sh
bash a5_cgh/scripts/eval_cot.sh
bash a5_cgh/scripts/eval_tot.sh 
```

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `MODEL_PATH` | `rl/outputs/train_lora_ppo_full/checkpoint-1304` | 模型 checkpoint |
| `OUTPUT_DIR` | `a5_cgh/outputs/eval_greedy` 或 `eval_cot` | 输出目录 |
| `LIMIT` | 0（全量） | 限制评测题数 |
| `BATCH_SIZE` | 4 | 批大小 |
| `GPU_ID` | 0 | GPU 编号 |
| `COT_INCLUDE_EXAMPLES` | 空 | 设为 1 启用 CoT few-shot 示例 |

## 输出产物

### Greedy → `a5_cgh/outputs/eval_greedy/`

```
mbpp_metrics_greedy.json      # pass@1、syntax、token、timing
mbpp_cases_greedy.jsonl       # 逐题评测结果
mbpp_greedy_records.jsonl     # 原始生成记录
token_cost.json
timing.json
mbpp_token_cost_per_task_greedy.jsonl
```

### CoT → `a5_cgh/outputs/eval_cot/`

```
mbpp_metrics_cot.json
mbpp_cases_cot.jsonl
mbpp_cot_records.jsonl
token_cost.json
timing.json
mbpp_token_cost_per_task_cot.jsonl
```

### ToT → `a5_cgh/outputs/eval_tot/`（已有）

```
mbpp_metrics_tot.json         # pass@1=6.23%, 257 题全量
token_cost.json               # avg 4681 tokens/task
timing.json                   # avg 26.1 s/task
```

## 代码结构

```
a5_cgh/
├── cot_code_example.py         # CoT Prompt 模板 + extract_final_code（与 tts/ 同名对齐）
├── baseline_common.py          # Greedy/CoT 单路径生成 + Token/Timing 统计
├── eval_common.py              # load_tokenizer / resolve_model_path
├── candidate_scoring.py        # ToT 候选打分（verifier）
├── mbpp_eval_baseline.py       # Greedy / CoT 评测主入口
├── mbpp_eval_tot.py            # ToT 评测
├── tree_of_thoughts.py         # ToT 搜索 + ToT token/timing 汇总
├── token_stats.py              # 单次 generate 的 token 计数
└── scripts/
    ├── eval_greedy.sh
    ├── eval_cot.sh
    └── eval_tot.sh
```

## Greedy vs CoT 区别

| 项目 | Greedy | CoT |
|------|--------|-----|
| Prompt | MBPP `[BEGIN]/[DONE]` 官方模板 | System + User 结构化 CoT |
| 代码抽取 | `extract_candidate_code`（[BEGIN] 后 / fenced block） | `extract_final_code`（Final code 区块） |
| max_new_tokens | 512 | 768 |
| 与 ToT 关系 | 成本下界（1 次前向） | 同一次前向，更长输出 |

## 跳过生成、仅重跑评测

若已有 records，可跳过模型推理：

```bash
SKIP_GENERATION=1 bash a5_cgh/scripts/eval_greedy.sh
SKIP_GENERATION=1 bash a5_cgh/scripts/eval_cot.sh
```
