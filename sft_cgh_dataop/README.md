# sft_cgh_dataop — 高质量数据筛选与高效 SFT（v1：强均衡砍到 ~4.3k）

> **对照 / 改进版请看 [`sft_cgh_dataop2/`](../sft_cgh_dataop2/)**：软过滤保留 ~10k + 签名注入 + 失败金标。本目录 v1 实验 pass@1≈22%，低于全量 baseline。

独立模块：根据 `infer_signature_cgh` 错误分析，用**更少但更高质量**的数据做 Full SFT。

**不修改**任何既有脚本/配置/数据；只读 `sft/data/`，产出全部在本目录。

## 为什么要做

推理签名设定下 pass@1 ≈ 24.9%，失败以**逻辑错误 / 部分通过 / 类型错误**为主。  
训练集摸底显示约 **12% 语法不可解析**、大量**无函数定义**脚本题、任务类型严重偏斜。  
→ 五维筛选后做「少而精」SFT，详见 [DATA_OPTIMIZATION_PLAN.md](./DATA_OPTIMIZATION_PLAN.md)。

## 目录

```text
sft_cgh_dataop/
├── DATA_OPTIMIZATION_PLAN.md
├── README.md
├── configs/
│   ├── filter_config.yaml
│   ├── qwen15_hq_sft_train.yaml
│   └── qwen15_hq_sft_predict.yaml
├── scripts/
│   ├── filter_high_quality.py
│   ├── run_filter.sh
│   ├── train.sh
│   ├── predict.sh
│   └── run_all.sh
├── data/                 # *_hq.json + dataset_info.json
└── outputs/
    ├── filter/           # filter_report.md/json
    ├── train/
    ├── predict/
    ├── eval/
    └── analysis/
```

## 快速开始

### 1) 只跑筛选（推荐先看报告）

```bash
cd /root/siton-tmp/assignment_A
bash sft_cgh_dataop/scripts/run_filter.sh
# 可选：控制最终 train 规模
TARGET_TRAIN_SIZE=4000 bash sft_cgh_dataop/scripts/run_filter.sh
```

查看：`sft_cgh_dataop/outputs/filter/filter_report.md`

### 2) 训练

```bash
GPU_ID=0 bash sft_cgh_dataop/scripts/train.sh
```

### 3) 评测（签名版 MBPP，便于与现有分析对比）

```bash
GPU_ID=0 bash sft_cgh_dataop/scripts/predict.sh
```

### 4) 一键流水线

```bash
GPU_ID=0 nohup bash sft_cgh_dataop/scripts/run_all.sh \
  > sft_cgh_dataop/outputs/nohup.log 2>&1 &
# 仅筛选、跳过训练：
SKIP_TRAIN=1 bash sft_cgh_dataop/scripts/run_all.sh
```

## 筛选维度

| 维度 | 做法 |
|------|------|
| 语法可解析性 | `ast.parse` 失败直接丢弃 |
| 输出长度 | 默认 60–2500 字符 |
| 任务完整性 | 必须有非 stub 的 `def`，括号平衡，拒绝截断尾 |
| 重复率 | exact / instruction / AST fingerprint 去重 |
| 任务类型均衡 | 分层抽样 + 质量分择优，默认目标 ~6000 条 train |

## 对照

| 设置 | 数据 | 预期 |
|------|------|------|
| Baseline Full SFT + infer signature | 全量 ~16.7k | pass@1 ≈ 24.9% |
| 本模块 HQ-SFT + 同协议评测 | 筛选后 ~4k–8k | 更少步数下接近或超过 baseline，syntax/空定义类下降 |
