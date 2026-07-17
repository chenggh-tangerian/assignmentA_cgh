# 高质量数据筛选与高效 SFT 优化方案

> 依据：`sft/infer_signature_cgh/outputs/analysis/error_analysis_full_sft_infer_signature.md`  
> 评测设定：Full SFT + 推理签名注入，pass@1 ≈ **24.9%**，语法通过率 ≈ **96.1%**  
> 原则：**不改动任何既有脚本/数据**；本模块只读引用 `sft/data/`，产出全部写入 `sft_cgh_dataop/`。

## 1. 错误分析 → 数据侧结论

| 失败类型 | 占失败 | 对训练数据的含义 |
|----------|--------|------------------|
| P0 逻辑错误 (assertion_failure) | 50.3% | 需要**正确、完整**的算法实现，而非脚本碎片或 stub |
| P1 部分通过 (partial_pass) | 18.6% | 目标函数体要覆盖边界/多断言，剔除半截代码 |
| P2 类型错误 | 11.9% | 保留含类型/边界语义的函数题；剔除无关脚本 |
| P2 函数名不匹配 | 6.7% | 强制保留带 `def` 的样本，强化「题目→具名函数」映射 |
| P2 语法错误 | 5.2% | **硬过滤** AST 不可解析、括号未闭合、截断输出 |
| 其余 runtime / timeout / attr | ~6% | 剔除空实现、死循环倾向极长样本 |

推理侧语法已较高（96%），剩余语法失败多来自**截断/不完整函数体**。训练集摸底（`code_sft_train.json`，16750 条）：

- AST 语法失败 ≈ **12%**
- 可解析但无 `def` ≈ **4251**（多为脚本/打印题，与 MBPP 不对齐）
- 任务类型严重偏斜：string / list 占多数，algo / regex / date 极少
- 精确近重复不多，但仍需去重防梯度浪费

→ 策略：**少而精**——先硬过滤脏样本，再按任务类型均衡抽样，用更少步数学到更贴近评测分布的映射。

## 2. 五维筛选策略

### 2.1 代码语法可解析性（硬门槛）

- 从 `output` 抽取 Python 代码（支持 \`\`\`python 围栏）
- `ast.parse` 必须成功
- 拒绝 `SyntaxError` / `IndentationError` 样本

**对应错误**：syntax_error；间接降低截断导致的空函数定义。

### 2.2 输出长度（硬门槛 + 软分）

默认（可在 `configs/filter_config.yaml` 调整）：

| 规则 | 默认 | 理由 |
|------|------|------|
| `min_output_chars` | 60 | 剔除 `print('hi')` 等过短噪声 |
| `max_output_chars` | 2500 | 剔除超长噪声/粘贴噪音，利于 `cutoff_len` |
| 软偏好区间 | 80–1200 | 与训练集 p10–p90 对齐，完整单函数题居多 |

**对应错误**：语法截断、过长低质样本稀释有效梯度。

### 2.3 任务完整性（硬门槛）

同时满足：

1. 至少包含一个 `FunctionDef` / `AsyncFunctionDef`（对齐 MBPP「生成函数」）
2. 函数体非空 stub（不能仅有 `pass` / `...` / 仅 docstring）
3. 括号/方括号/花括号栈平衡
4. 末行不像未写完的控制结构（`def/if/for/...` 结尾无后继）

**对应错误**：partial_pass、syntax_error（空定义）、function_name_mismatch（无 def 的脚本）。

### 2.4 重复率（硬去重）

三级去重（保留首次出现）：

1. **精确**：`(instruction, input, output)` 哈希
2. **指令级**：相同 `instruction`（忽略大小写）只留质量分最高的一条
3. **代码指纹**：规范化 AST dump / 去空白后的 code hash，抑制换皮重复

**对应问题**：重复样本浪费 epoch，拉高多数类权重。

### 2.5 任务类型均衡性（分层抽样）

启发式标签（基于 instruction + code 关键词）：

`string | list_array | math_number | dict_set | algo_search | file_io | class_oop | regex | date_time | other`

流程：

1. 通过 2.1–2.4 后得到候选池
2. 统计各类数量；对超大类按 `max_per_type`（或目标总量 `target_train_size`）**降采样**
3. 稀有类尽量全留；同类内按 **质量分** 排序保留

质量分（软，用于同类择优）：

- 有非 stub 函数 +2
- 有 docstring +1
- 长度落在偏好区间 +1
- instruction 含边界词（empty / None / edge / zero …）+1
- 输出过短/过长 -1

**对应错误**：P0 逻辑题需要更多 algo/math；同时避免 string 类淹没梯度。

## 3. 预期数据规模

| 阶段 | 规模（约） | 说明 |
|------|------------|------|
| 原始 train | 16750 | `sft/data/code_sft_train.json`（只读） |
| 硬过滤后 | ~9k–11k | 去语法坏例 + 无函数 + 长度 |
| 均衡后默认 | **4k–8k** | `target_train_size` 可配；默认偏「少而精」 |
| valid | 同步过滤 | 保证 eval 分布一致，不做激进降采样 |

目标：在相近或更少训练步数下，提升 pass@1，并观察 assertion_failure / syntax_error 占比下降。

## 4. 实验对照建议

| 实验 | 数据 | 目的 |
|------|------|------|
| Baseline | 全量 `code_sft_*` | 已有 Full SFT ≈24.9%（+infer signature） |
| HQ-SFT（本模块） | `sft_cgh_dataop/data/code_sft_*_hq.json` | 验证「更少更高质」 |
| 消融 | 只开语法过滤 / 只开均衡 | 看哪一维贡献最大 |

评测建议继续用 **推理签名** 设定（与分析报告同源），便于对比 category 分布。

## 5. 本模块产物

```text
sft_cgh_dataop/
├── DATA_OPTIMIZATION_PLAN.md   # 本文档
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
├── data/                       # 筛选后数据集 + dataset
└── outputs/
    ├── filter/                 # 筛选报告
    ├── train|predict|eval|analysis/
```

## 6. 与既有模块边界

- **不修改**：`sft/scripts/`、`sft/configs/`、`sft/data/`、`sft/infer_signature_cgh/` 等任何既有文件
- **只读引用**：原始 Alpaca 划分、MBPP 评测脚本、错误分析报告
- **可写范围**：仅 `sft_cgh_dataop/`
