# 代码修复式 SFT 扩展

`sft_cgh2` 是一个独立的代码修复 SFT 扩展模块，用来展示“根据执行反馈修正错误代码”的训练任务。它不依赖修改原有 `sft`、`dpo` 或已有实验脚本，所有新增数据、配置和输出都放在 `sft_cgh2` 下。

## 任务设计

这个任务不是让模型从零生成代码，而是让模型看到：

`题目描述 + 错误代码 + 失败测试用例/报错信息 -> 修复后代码`

也就是说，模型需要根据已有错误实现和执行反馈，输出一份能通过测试的修复后 Python 代码。

每条样本仍然使用项目里已有的 Alpaca 三字段格式，方便直接被 LLaMA-Factory 读取：

```json
{
  "instruction": "Fix the buggy Python code so that it satisfies the programming task and passes the failing tests.",
  "input": "### Problem\n...\n\n### Buggy Code\n```python\n...\n```\n\n### Failing Tests / Error Messages\n...",
  "output": "def fixed_solution(...):\n    ..."
}
```

其中：

- `instruction`：固定告诉模型执行代码修复任务。
- `input`：包含题目描述、错误代码、失败测试和报错信息。
- `output`：参考修复代码，也就是训练目标。

## 数据构建流程

1. 读取 MBPP 评测结果，例如：
   `sft/lora2_exp_cgh/outputs/r8_tqv_q4/eval/mbpp_cases.jsonl`
2. 默认只保留没有通过测试的失败样本。
3. 从每条失败样本中提取：
   - `prompt`：题目描述
   - `code` 或 `predict`：模型生成的错误代码
   - `test_results`：失败测试、断言、报错栈
   - `reference_code`：参考修复代码
4. 生成 `repair_sft_train.json` 和 `repair_sft_valid.json`。
5. 写入独立的 `dataset_info.json`，供 LLaMA-Factory 训练使用。

## 构建数据

在项目根目录执行：

```bash
python sft_cgh2/scripts/build_repair_sft.py \
  --cases sft/lora2_exp_cgh/outputs/r8_tqv_q4/eval/mbpp_cases.jsonl \
  --output-dir sft_cgh2/data
```

可选参数：

- `--valid-ratio 0.1`：验证集比例。
- `--seed 42`：随机打乱种子，保证可复现。
- `--max-feedback-chars 2400`：每条样本中最多保留多少报错字符。
- `--max-failed-tests 3`：每条样本最多展示几个失败测试。
- `--include-passing`：额外包含已经通过的样本，作为“无需修复/等价修复”样本；默认不开启。

当前已经基于 `r8_tqv_q4` 的 MBPP 评测结果生成了：

- `sft_cgh2/data/repair_sft_train.json`：223 条训练样本
- `sft_cgh2/data/repair_sft_valid.json`：25 条验证样本
- `sft_cgh2/data/repair_sft_all.json`：248 条总样本

## 是否需要训练

如果只是展示这个扩展任务的数据组织方式，不一定要训练。现在的数据已经能说明任务形式：模型输入错误代码和失败反馈，输出修复后代码。

如果你想验证这个任务是否真的能提升“根据报错修代码”的能力，就需要训练。训练会让模型学习这类映射关系：

```text
错误函数名 / 逻辑错误 / 语法错误 / 类型错误 + 失败测试反馈 -> 修复后的代码
```

## 训练

```bash
/opt/conda/envs/chenggh-sft/bin/python -m llamafactory.cli train \
  sft_cgh2/configs/qwen15_repair_lora_train.yaml
```

这个配置是一个保守的 QLoRA 起点：

- 基座模型：`./Qwen1.5-0.5B-Chat`
- 训练数据：`repair_sft_train`
- 验证数据：`repair_sft_valid`
- 输出目录：`sft_cgh2/outputs/qwen15_repair_lora`
- 不会写入原有 `sft` 实验目录。

## 预测与检查

训练完成后，可以在验证集修复提示上做预测：

```bash
/opt/conda/envs/chenggh-sft/bin/python -m llamafactory.cli train \
  sft_cgh2/configs/qwen15_repair_lora_predict.yaml
```

预测结果会写入：

`sft_cgh2/outputs/qwen15_repair_lora_predict`

## 展示重点

- 这个模块不是替换原来的代码生成 SFT，而是补充一个“执行反馈驱动的代码修复”任务。
- 样本里保留了失败测试和报错信息，训练目标更接近真实调试场景。
- 长 traceback 会被截断，避免超过 `cutoff_len`。
- 修复目标来自 MBPP 评测 case 中的 `reference_code`。
