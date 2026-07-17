# sft_cgh_dataop3 数据报告（公平，~60% 规模）

## 约束
- 训练样本 **只** 来自 `sft/data/code_sft_train.json`
- **未** 将 MBPP / cases / reference 混入 train
- 目标规模 ≈ raw×60% = 10050
- 最终 train = **10050**（60.0% of raw）

## Train
- 原始: 16750
- 软过滤+去重: 9847
- 定向加码 extras: 203
- 最终: 10050
- 签名注入: 10044
- 标签分布: {'other': 4580, 'type_like': 3518, 'algo_like': 2730, 'boundary_like': 835}

## Valid
- 最终: 556（sft/data valid 软过滤全留）
