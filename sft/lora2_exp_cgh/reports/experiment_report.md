# LoRA2 / QLoRA SFT 超参数实验报告

生成时间：2026-07-14T07:59:05.940948+00:00

## 总览

- 实验组数：**13**
- 已完成：**13**
- 失败：**0**
- 待运行/进行中：**0**
- Phase1 最优配置：**`r8_tqv_q4`**

## Baseline 对照（全量 SFT，不重新训练）

- pass@1：**1.95%**
- 语法通过率：**95.72%**
- 数据来源：`/root/siton-tmp/assignment_A/sft/outputs/eval_mbpp/mbpp_metrics.json`

### Baseline 训练速度

- 训练耗时：**7309.34** 秒
- 步/秒：**0.86**

## Phase1 主网格结果

| 实验ID | 类型 | rank | alpha | dropout | target | quant | lr | epoch | pass@1 | 峰值显存MiB | 步/秒 | 可训练参数 | 训练损失 | 状态 |
|--------|------|------|-------|---------|--------|-------|-----|-------|--------|-------------|-------|------------|----------|------|
| r16_tall_q4 | qlora | 16 | 32 | 0.05 | 全部层 | 4bit(QLoRA) | 0.0001 | 3.0 | 3.11% | 11495 | 0.60 | 7569408 | 0.75 | 全部完成 |
| r16_tall_qnone | lora | 16 | 32 | 0.05 | 全部层 | 无(LoRA) | 0.0001 | 3.0 | 2.72% | 19133 | 0.44 | 7569408 | 0.74 | 全部完成 |
| r16_tqv_q4 | qlora | 16 | 32 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 3.0 | 2.33% | 11395 | 0.78 | 1572864 | 0.83 | 全部完成 |
| r16_tqv_qnone | lora | 16 | 32 | 0.05 | q/v投影 | 无(LoRA) | 0.0001 | 3.0 | 2.72% | 12089 | 1.08 | 1572864 | 0.81 | 全部完成 |
| r8_tall_q4 | qlora | 8 | 16 | 0.05 | 全部层 | 4bit(QLoRA) | 0.0001 | 3.0 | 2.72% | 14271 | 0.54 | 3784704 | 0.78 | 全部完成 |
| r8_tall_qnone | lora | 8 | 16 | 0.05 | 全部层 | 无(LoRA) | 0.0001 | 3.0 | 2.72% | 12125 | 0.75 | 3784704 | 0.76 | 全部完成 |
| r8_tqv_q4 | qlora | 8 | 16 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 3.0 | 3.50% | 11381 | 0.85 | 786432 | 0.85 | 全部完成 |
| r8_tqv_qnone | lora | 8 | 16 | 0.05 | q/v投影 | 无(LoRA) | 0.0001 | 3.0 | 3.11% | 12125 | 1.09 | 786432 | 0.82 | 全部完成 |

## Phase2 Alpha Sweep 结果

| 实验ID | 类型 | rank | alpha | dropout | target | quant | lr | epoch | pass@1 | 峰值显存MiB | 步/秒 | 可训练参数 | 训练损失 | 状态 |
|--------|------|------|-------|---------|--------|-------|-----|-------|--------|-------------|-------|------------|----------|------|
| r8_tqv_q4_alpha_a1x | qlora | 8 | 8 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 3.0 | 3.89% | 11381 | 0.85 | 786432 | 0.86 | 全部完成 |
| r8_tqv_q4_alpha_a2x | qlora | 8 | 16 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 3.0 | 3.50% | 11381 | 0.85 | 786432 | 0.85 | 引用 `r8_tqv_q4` |
| r8_tqv_q4_alpha_a4x | qlora | 8 | 32 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 3.0 | 2.72% | 11381 | 0.85 | 786432 | 0.84 | 全部完成 |

## Phase3 Epoch Sweep 结果

| 实验ID | 类型 | rank | alpha | dropout | target | quant | lr | epoch | pass@1 | 峰值显存MiB | 步/秒 | 可训练参数 | 训练损失 | 状态 |
|--------|------|------|-------|---------|--------|-------|-----|-------|--------|-------------|-------|------------|----------|------|
| r8_tqv_q4_epoch_1 | qlora | 8 | 16 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 1.0 | 3.50% | 11379 | 0.75 | 786432 | 0.88 | 全部完成 |
| r8_tqv_q4_epoch_5 | qlora | 8 | 16 | 0.05 | q/v投影 | 4bit(QLoRA) | 0.0001 | 5.0 | 2.72% | 11381 | 0.85 | 786432 | 0.83 | 全部完成 |

## 作业要求覆盖检查

| 要求 | 配置/实验 | 记录位置 |
|------|-----------|----------|
| LoRA/QLoRA 微调 | `finetuning_type` + `quantization_bit` | `configs/*_train.yaml`, `state/runs/*.json` params |
| lora_rank | Phase1 grid {8,16} | params + 报告 |
| lora_alpha | Phase1: 2×rank；Phase2 sweep {1×,2×,4×}rank | params + 报告 |
| lora_dropout | 固定 0.05 | params + 报告 |
| lora_target | q_proj,v_proj / all | params + 报告 |
| quantization_bit | none(LoRA) / 4(QLoRA) | params + 报告 |
| learning_rate | 1e-4；Phase2/3 随最优配置 | params + 报告 |
| epoch | Phase1: 3；Phase3 sweep {1,5} | params + 报告 |
| 显存占用 | 峰值 MiB | `logs/<run>/gpu_memory.csv` → resources |
| 训练速度 | steps/sec, samples/sec | `train_results.json` → resources |
| 参数量 | trainable/all params | 训练日志 → resources |
| 最终测试结果 | MBPP pass@1 等 | `outputs/<run>/eval/mbpp_metrics.json` → metrics |

## 各组详情

### `r16_tall_q4`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=16, alpha=32, dropout=0.05, target=all, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：30322120
  - Adapter 体积(MB)：28.9174
  - 总参数量：471557120
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7283162474632263
  - 训练平均显存(MiB)：11477.63
  - 训练峰值显存(MiB)：11495
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：2062
  - gpu_util_peak_pct：100
  - 超参快照：{'lora_rank': 16, 'lora_alpha': 32, 'lora_dropout': 0.05, 'lora_target': 'all', 'lora_target_key': 'all', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.753241239014191
  - 训练耗时(秒)：10377.0279
  - 训练样本/秒：4.842
  - 训练步/秒：0.605
  - 可训练参数量：7569408
  - 可训练参数占比(%)：1.6052
- 评测：
  - avg_code_token_f1：0.4849695287966863
  - 测试用例通过率：3.35%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.11%
  - 通过任务数：8
  - 通过用例数：26
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r16_tall_q4/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：96.11%
  - 测试用例总数：776

### `r16_tall_qnone`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=16, alpha=32, dropout=0.05, target=all, quant=无(LoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：30322120
  - Adapter 体积(MB)：28.9174
  - 总参数量：471557120
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7158302664756775
  - 训练平均显存(MiB)：13531.67
  - 训练峰值显存(MiB)：19133
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：2831
  - gpu_util_peak_pct：100
  - 超参快照：{'lora_rank': 16, 'lora_alpha': 32, 'lora_dropout': 0.05, 'lora_target': 'all', 'lora_target_key': 'all', 'quantization_bit': None, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'lora'}
  - 训练损失：0.737863412084795
  - 训练耗时(秒)：14284.0225
  - 训练样本/秒：3.518
  - 训练步/秒：0.44
  - 可训练参数量：7569408
  - 可训练参数占比(%)：1.6052
- 评测：
  - avg_code_token_f1：0.48327780570488155
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r16_tall_qnone/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：96.89%
  - 测试用例总数：776

### `r16_tqv_q4`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=16, alpha=32, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：6304192
  - Adapter 体积(MB)：6.0121
  - 总参数量：465560576
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7624239921569824
  - 训练平均显存(MiB)：11374.32
  - 训练峰值显存(MiB)：11395
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1597
  - gpu_util_peak_pct：100
  - 超参快照：{'lora_rank': 16, 'lora_alpha': 32, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.8315408931952
  - 训练耗时(秒)：8039.8688
  - 训练样本/秒：6.25
  - 训练步/秒：0.781
  - 可训练参数量：1572864
  - 可训练参数占比(%)：0.3378
- 评测：
  - avg_code_token_f1：0.46007847411632374
  - 测试用例通过率：2.58%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.33%
  - 通过任务数：6
  - 通过用例数：20
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r16_tqv_q4/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.16%
  - 测试用例总数：776

### `r16_tqv_qnone`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=16, alpha=32, dropout=0.05, target=q_proj,v_proj, quant=无(LoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：6304192
  - Adapter 体积(MB)：6.0121
  - 总参数量：465560576
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.744908332824707
  - 训练平均显存(MiB)：12057.36
  - 训练峰值显存(MiB)：12089
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1158
  - gpu_util_peak_pct：100
  - 超参快照：{'lora_rank': 16, 'lora_alpha': 32, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': None, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'lora'}
  - 训练损失：0.8107511238169799
  - 训练耗时(秒)：5820.9485
  - 训练样本/秒：8.633
  - 训练步/秒：1.079
  - 可训练参数量：1572864
  - 可训练参数占比(%)：0.3378
- 评测：
  - avg_code_token_f1：0.4712434923358447
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r16_tqv_qnone/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：93.39%
  - 测试用例总数：776

### `r8_tall_q4`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=all, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：15182728
  - Adapter 体积(MB)：14.4794
  - 总参数量：467772416
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7333711385726929
  - 训练平均显存(MiB)：11735.53
  - 训练峰值显存(MiB)：14271
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：2315
  - gpu_util_peak_pct：100
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'all', 'lora_target_key': 'all', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.7811951795530638
  - 训练耗时(秒)：11662.2197
  - 训练样本/秒：4.309
  - 训练步/秒：0.539
  - 可训练参数量：3784704
  - 可训练参数占比(%)：0.8091
- 评测：
  - avg_code_token_f1：0.48310520664760703
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tall_q4/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.94%
  - 测试用例总数：776

### `r8_tall_qnone`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=all, quant=无(LoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：15182728
  - Adapter 体积(MB)：14.4794
  - 总参数量：467772416
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7197490334510803
  - 训练平均显存(MiB)：12102.79
  - 训练峰值显存(MiB)：12125
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1675
  - gpu_util_peak_pct：33
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'all', 'lora_target_key': 'all', 'quantization_bit': None, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'lora'}
  - 训练损失：0.7643293258833377
  - 训练耗时(秒)：8419.6071
  - 训练样本/秒：5.968
  - 训练步/秒：0.746
  - 可训练参数量：3784704
  - 可训练参数占比(%)：0.8091
- 评测：
  - avg_code_token_f1：0.4764764932953747
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tall_qnone/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.55%
  - 测试用例总数：776

### `r8_tqv_q4`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7730488181114197
  - 训练平均显存(MiB)：11358.4
  - 训练峰值显存(MiB)：11381
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1469
  - gpu_util_peak_pct：31
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.8466210446703856
  - 训练耗时(秒)：7385.8257
  - 训练样本/秒：6.804
  - 训练步/秒：0.851
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.4633188721315931
  - 测试用例通过率：3.74%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.50%
  - 通过任务数：9
  - 通过用例数：29
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.94%
  - 测试用例总数：776

### `r8_tqv_q4_alpha_a1x`

- 阶段：**Phase2 Alpha Sweep** | 状态：**全部完成**
- 超参：rank=8, alpha=8, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7803059816360474
  - 训练平均显存(MiB)：11350.6
  - 训练峰值显存(MiB)：11381
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1466
  - gpu_util_peak_pct：35
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 8, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora', 'alpha_multiplier': 1}
  - 训练损失：0.8570380920401351
  - 训练耗时(秒)：7366.3147
  - 训练样本/秒：6.822
  - 训练步/秒：0.853
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.45702169258095365
  - 测试用例通过率：4.12%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.89%
  - 通过任务数：10
  - 通过用例数：32
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4_alpha_a1x/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：93.77%
  - 测试用例总数：776

### `r8_tqv_q4_alpha_a2x`

- 阶段：**Phase2 Alpha Sweep** | 状态：**全部完成**
- 引用已有 run：`r8_tqv_q4`（跳过重复训练）
- 超参：rank=8, alpha=16, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7730488181114197
  - 训练平均显存(MiB)：11358.4
  - 训练峰值显存(MiB)：11381
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1469
  - gpu_util_peak_pct：31
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.8466210446703856
  - 训练耗时(秒)：7385.8257
  - 训练样本/秒：6.804
  - 训练步/秒：0.851
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.4633188721315931
  - 测试用例通过率：3.74%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.50%
  - 通过任务数：9
  - 通过用例数：29
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.94%
  - 测试用例总数：776

### `r8_tqv_q4_alpha_a4x`

- 阶段：**Phase2 Alpha Sweep** | 状态：**全部完成**
- 超参：rank=8, alpha=32, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.766246497631073
  - 训练平均显存(MiB)：11358.34
  - 训练峰值显存(MiB)：11381
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：1465
  - gpu_util_peak_pct：76
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 32, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'qlora', 'alpha_multiplier': 4}
  - 训练损失：0.8351778647050248
  - 训练耗时(秒)：7366.9668
  - 训练样本/秒：6.821
  - 训练步/秒：0.853
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.46483147295908167
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4_alpha_a4x/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.16%
  - 测试用例总数：776

### `r8_tqv_q4_epoch_1`

- 阶段：**Phase3 Epoch Sweep** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=1.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：1.0
  - 验证准确率：None
  - 验证损失：0.7967978119850159
  - 训练平均显存(MiB)：11321.94
  - 训练峰值显存(MiB)：11379
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：568
  - gpu_util_peak_pct：99
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 1.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.8821313722768964
  - 训练耗时(秒)：2802.7491
  - 训练样本/秒：5.976
  - 训练步/秒：0.747
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.4436416816870453
  - 测试用例通过率：3.74%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.50%
  - 通过任务数：9
  - 通过用例数：29
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4_epoch_1/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：94.55%
  - 测试用例总数：776

### `r8_tqv_q4_epoch_5`

- 阶段：**Phase3 Epoch Sweep** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=q_proj,v_proj, quant=4bit(QLoRA), lr=0.0001, epoch=5.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：5.0
  - 验证准确率：None
  - 验证损失：0.7636119723320007
  - 训练平均显存(MiB)：11367.41
  - 训练峰值显存(MiB)：11381
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：2444
  - gpu_util_peak_pct：87
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': 4, 'learning_rate': 0.0001, 'num_train_epochs': 5.0, 'finetuning_type': 'qlora'}
  - 训练损失：0.8255922959436091
  - 训练耗时(秒)：12327.3203
  - 训练样本/秒：6.794
  - 训练步/秒：0.849
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.45959187799646034
  - 测试用例通过率：2.96%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：2.72%
  - 通过任务数：7
  - 通过用例数：23
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_q4_epoch_5/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：93.77%
  - 测试用例总数：776

### `r8_tqv_qnone`

- 阶段：**Phase1 主网格** | 状态：**全部完成**
- 超参：rank=8, alpha=16, dropout=0.05, target=q_proj,v_proj, quant=无(LoRA), lr=0.0001, epoch=3.0
- 资源：
  - adapter_size_bytes：3158328
  - Adapter 体积(MB)：3.012
  - 总参数量：464774144
  - 训练轮数：3.0
  - 验证准确率：None
  - 验证损失：0.7542381882667542
  - 训练平均显存(MiB)：10116.09
  - 训练峰值显存(MiB)：12125
  - gpu_memory_total_mib：23552
  - gpu_monitor_samples：5035
  - gpu_util_peak_pct：36
  - 超参快照：{'lora_rank': 8, 'lora_alpha': 16, 'lora_dropout': 0.05, 'lora_target': 'q_proj,v_proj', 'lora_target_key': 'qv', 'quantization_bit': None, 'learning_rate': 0.0001, 'num_train_epochs': 3.0, 'finetuning_type': 'lora'}
  - 训练损失：0.8245945873817643
  - 训练耗时(秒)：5762.9751
  - 训练样本/秒：8.719
  - 训练步/秒：1.09
  - 可训练参数量：786432
  - 可训练参数占比(%)：0.1692
- 评测：
  - avg_code_token_f1：0.4652104320729253
  - 测试用例通过率：3.48%
  - benchmark：MBPP
  - config：sanitized
  - exact_match：0.0
  - mbpp_dir：/root/siton-tmp/mbpp
  - note：Reports pass@1 using MBPP sanitized task tests and execution outputs.
  - 任务总数：257
  - pass@1（任务通过率）：3.11%
  - 通过任务数：8
  - 通过用例数：27
  - predictions：/root/siton-tmp/assignment_A/sft/lora2_exp_cgh/outputs/r8_tqv_qnone/predict/generated_predictions.jsonl
  - split：test
  - 语法通过率：95.72%
  - 测试用例总数：776

## 断点续跑

详见 `sft/lora2_exp_cgh/README.md`。

