# sft_cgh_dataop3 — 公平数据优化方案（禁止测试集）

> **硬约束**：只允许在 `sft/data` 的 train/valid 上下手。  
> **绝对禁止**：MBPP test / 评测 cases / `reference_code` / 失败题原题 进入训练集。  
> dataop2 的「失败金标」做法已废弃，本目录不继承。

错误分析（`infer_signature_cgh` / dataop v1）**只当诊断信号**，用来决定「在训练集里多捞哪类样本」，不当作训练样本来源。

---

## 1. 诊断回顾（为何改数据）

签名评测下失败主因（v1 / baseline）：

| 优先级 | 错误类型 | 数据侧应对（仅用 train） |
|--------|----------|--------------------------|
| P0 | 逻辑错误 / 部分通过 | 上采样 train 里算法/实现完整的函数题 |
| P2 | 类型错误 | 上采样含类型/转换语义的样本 |
| P2 | 边界条件 | 上采样含 empty/None/edge 等边界词的样本 |
| P2 | 函数名不匹配 | **训练侧注入函数签名**（从该条 train 的 `output` 抽 `def`，不是测试集） |
| P2 | 语法/截断 | 软过滤：AST 可解析 + 非 stub `def` + 长度门控 |

---

## 2. 三步配方（全部来自 `sft/data`）

### Step A — 软过滤（去脏，不狂砍）

对 `sft/data/code_sft_{train,valid,test}.json`：

- `ast.parse` 通过  
- 至少一个非 stub 的 `FunctionDef`  
- output 长度 ∈ [60, 2500]  
- exact / instruction / code-fingerprint 去重  
- **不做**按任务类型把多数类砍到 900（v1 已证伪）

摸底：train 软过滤后约 **~10.0k**（全量 16.7k 的 ~60%）。

### Step B — 训练侧签名注入（仍是 train 自己的签名）

对每条保留样本，从**本条 `output`** 解析：

```text
def foo(...):
```

追加到 instruction（与评测 prompt 格式对齐）。  
这不引入测试题，只规范「看见签名 → 写出同名函数」。

### Step C — 按错误原因，在训练集内定向加码（不上测试题）

用 **instruction+code 关键词** 给 train 样本打弱标签（仅启发式）：

| 标签 | 服务的失败类型 | 触发词示例 |
|------|----------------|------------|
| `algo_like` | 逻辑 / 部分通过 | sort, search, recursive, prime, matrix, gcd, binary… |
| `type_like` | 类型错误 | int/str/list/dict、isinstance、cast… |
| `boundary_like` | 边界错误 | empty, None, edge, zero, single… |

操作（可调）：

1. 软过滤 + 签名后的集合记为 `S`（~10k）  
2. 从 `S` 中取出三类子集，各 **额外再复制 1 份** 混入（仍是同一条 train 样本，只是提高见到的频率）  
3. 最终大致：

```text
final ≈ |S| + |algo∩S| + |type∩S| + |boundary∩S|
      ≈ 10k + ~2.4k + ~3.4k + ~0.8k
      ≈ 16k–17k（有重叠会略少；去重策略：允许定向标签重复，不做全局 exact 去重杀掉上采样）
```

若担心体积，可改为每类 **top-quality 抽样最多 N 条再 ×2**，而不是全量复制。

**不做的事**：

- ❌ 读取 `mbpp_*` / `*_cases.jsonl` / `error_cases_enriched*` 的题面或 reference  
- ❌ 任何 test split 的 instruction/output 进入 train  
- ❌ 用评测集做 retrieval 近邻增强（也算泄漏风险）

---

## 3. 与前两版对照

| 目录 | 做法 | 是否公平 | 结果 |
|------|------|----------|------|
| `sft_cgh_dataop` | 硬过滤 + 类型狂砍 → 4.3k | ✅ | ~22% < baseline 24.9% |
| `sft_cgh_dataop2` | 软过滤 + 签名 + **测试集金标** | ❌ 泄漏 | ~86%（无效） |
| **`sft_cgh_dataop3`** | 软过滤 + 签名 + **仅 train 内按错误类型加码** | ✅ | 待训 |

成功标准（签名版 MBPP，与之前同协议）：

- 主目标：pass@1 **≥ baseline 24.9%**  
- 更理想：稳定到 **26–30%**（不保证）  
- 语法率不掉、function_name_mismatch 下降

---

## 4. 目录与命令（同意后再训）

```text
sft_cgh_dataop3/
├── DATA_PLAN.md          # 本文
├── README.md
├── configs/
├── scripts/build_data.py # 只读 sft/data
├── scripts/train.sh
├── scripts/predict.sh
├── data/                 # 本模块生成
└── outputs/              # 训练/评测
```

```bash
# 1) 造数据（只碰 sft/data）
bash sft_cgh_dataop3/scripts/build_data.sh

# 2) 你确认报告后再训
GPU_ID=0 nohup bash sft_cgh_dataop3/scripts/train.sh \
  > sft_cgh_dataop3/outputs/nohup_train.log 2>&1 &
```

构建报告会写明：源文件路径、过滤统计、各类加码条数，并 **显式断言未读取任何 MBPP/cases 文件**。

---

## 5. 已拍板配置（执行版）

- 规模目标：约 **全量 train 的 60%**（16750 × 0.6 ≈ **10050**）
- 做法：软过滤几乎全留（~9847）+ 训练集内轻度加码（algo/type/boundary）
- **禁止**测试集进训练
- 不做消融
