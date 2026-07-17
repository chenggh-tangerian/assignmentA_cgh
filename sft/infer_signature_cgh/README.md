# Full SFT + 推理时签名注入（infer_signature_cgh）

独立模块：只在 **推理/评测 prompt** 里加函数签名，**不改训练数据、不改权重**。

不修改：
- `sft/scripts/`
- `sft/configs/`
- `sft/data/`（只读引用 `mbpp_sanitized_test.json`）
- `sft/outputs/qwen15_code_full_sft/`（只读加载）

## 目录

```
sft/infer_signature_cgh/
├── README.md
├── configs/qwen15_full_sft_predict_with_signature.yaml
├── scripts/
│   ├── predict.sh
│   └── run_all.sh          # 造数据 → 推理 → 评测 → 错误分析
├── data/                   # 签名版 MBPP 评测集（本模块生成）
└── outputs/
    ├── predict/
    ├── eval/
    └── analysis/
```

## 运行

```bash
cd /root/siton-tmp/assignment_A
GPU_ID=0 nohup bash sft/infer_signature_cgh/scripts/run_all.sh \
  > sft/infer_signature_cgh/outputs/nohup.log 2>&1 &
tail -f sft/infer_signature_cgh/outputs/run.log
```

## 对照

| 设置 | 模型 | prompt | 预期 |
|------|------|--------|------|
| Baseline | Full SFT | 无签名 | ~3% pass@1 |
| 本模块 | Full SFT（同上） | 推理加签名 | ~24%+ pass@1 |
