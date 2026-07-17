# 高质量数据筛选报告

依据错误分析中的 P0/P1/P2 失败模式，按语法可解析性、输出长度、任务完整性、重复率、任务类型均衡性筛选。

## 配置摘要

- 输出长度: [60, 2500]
- 要求函数定义: True；拒绝 stub: True
- 去重: exact=True, instruction=True, code_fp=True
- 均衡抽样: enable=True, target_train_size=6000
- seed: 42

## Split: `train`

| 阶段 | 数量 |
|------|------|
| 输入 | 16750 |
| 硬过滤通过 | 10010 |
| 去重后 | 9847 |
| **最终保留** | **4265** (25.5%) |
| 平均质量分 | 3.628 |
| 平均 output 长度 | 336.9 |

### 硬过滤拒绝原因

| 原因 | 数量 |
|------|------|
| no_function_def | 3631 |
| syntax_error | 1856 |
| output_too_short | 942 |
| output_too_long | 296 |
| stub_only | 12 |
| trailing_incomplete | 3 |

### 去重

| 原因 | 数量 |
|------|------|
| code_fingerprint_dup | 144 |
| instruction_dup | 19 |

### 任务类型分布（最终）

| 类型 | 数量 |
|------|------|
| string | 900 |
| math_number | 900 |
| list_array | 900 |
| other | 359 |
| class_oop | 353 |
| file_io | 315 |
| dict_set | 311 |
| algo_search | 155 |
| date_time | 63 |
| regex | 9 |

## Split: `valid`

| 阶段 | 数量 |
|------|------|
| 输入 | 930 |
| 硬过滤通过 | 556 |
| 去重后 | 556 |
| **最终保留** | **556** (59.8%) |
| 平均质量分 | 3.507 |
| 平均 output 长度 | 336.3 |

### 硬过滤拒绝原因

| 原因 | 数量 |
|------|------|
| no_function_def | 210 |
| syntax_error | 88 |
| output_too_short | 51 |
| output_too_long | 23 |
| trailing_incomplete | 1 |
| stub_only | 1 |

### 去重

_无显著重复_

### 任务类型分布（最终）

| 类型 | 数量 |
|------|------|
| string | 213 |
| list_array | 157 |
| math_number | 86 |
| file_io | 25 |
| dict_set | 24 |
| other | 20 |
| class_oop | 18 |
| algo_search | 9 |
| regex | 2 |
| date_time | 2 |

## Split: `test`

| 阶段 | 数量 |
|------|------|
| 输入 | 932 |
| 硬过滤通过 | 575 |
| 去重后 | 575 |
| **最终保留** | **575** (61.7%) |
| 平均质量分 | 3.508 |
| 平均 output 长度 | 345.2 |

### 硬过滤拒绝原因

| 原因 | 数量 |
|------|------|
| no_function_def | 197 |
| syntax_error | 96 |
| output_too_short | 51 |
| output_too_long | 13 |

### 去重

_无显著重复_

### 任务类型分布（最终）

| 类型 | 数量 |
|------|------|
| string | 208 |
| list_array | 170 |
| math_number | 100 |
| class_oop | 30 |
| other | 22 |
| dict_set | 18 |
| file_io | 18 |
| algo_search | 8 |
| date_time | 1 |

## 与错误分析的对应关系

- `syntax_error` / `no_function_def` / `trailing_incomplete` → 压低评测中的语法错误与空定义
- 强制 `def` + 非 stub → 强化函数命名与完整实现，缓解 function_name_mismatch / partial_pass
- 类型均衡 + 边界词加分 → 服务 P0 逻辑题与 P2 类型/边界错误
- 去重 + 控规模 → 用更少样本做高效 SFT，减少多数类过拟合
