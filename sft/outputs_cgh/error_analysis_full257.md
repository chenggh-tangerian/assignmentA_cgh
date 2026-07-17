# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-11T09:20:38.054932+00:00
- 数据来源: `sft/outputs/eval_mbpp/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 5，失败 252）
- 部分通过用例: 2
- 全量 pass@1 (metrics): **3.11%**
- 全量语法通过率 (metrics): **95.33%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 函数名不匹配 | 228 | 88.7% | 90.5% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 语法错误 | 13 | 5.1% | 5.2% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 逻辑错误(断言失败) | 5 | 1.9% | 2.0% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 类型错误 | 3 | 1.2% | 1.2% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 部分测试通过 | 2 | 0.8% | 0.8% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 其他运行时错误 | 1 | 0.4% | 0.4% | 人工抽查 stderr，归入更细类别后补充规则。 |

## 优先改进项 (按失败占比)

- **P0 函数名不匹配**: 228 例 (90.5% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P2 语法错误**: 13 例 (5.2% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P3 逻辑错误(断言失败)**: 5 例 (2.0% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P3 类型错误**: 3 例 (1.2% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P3 部分测试通过**: 2 例 (0.8% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P3 其他运行时错误**: 1 例 (0.4% 失败) — 人工抽查 stderr，归入更细类别后补充规则。

## 典型样例

### 函数名不匹配 (function_name_mismatch)
- task_id=11: 定义 `['remove_first_last_occurrence']` vs 期望 `['remove_Occ']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_qlix9228/candidate_test.py", line 7, in <module>     assert re`
- task_id=12: 定义 `['sortMatrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_d4f4_vwg/candidate_test.py", line 9, in <module>     assert so`
- task_id=14: 定义 `['triangular_prism_volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ta9s18x7/candidate_test.py", line 8, in <module>     assert fi`

### 语法错误 (syntax_error)
- task_id=97: 定义 `[]` vs 期望 `['frequency_lists']`
- task_id=129: 定义 `['is_magic_square']` vs 期望 `['magic_square_test']`
- task_id=142: 定义 `[]` vs 期望 `['count_samepair']`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval__z_6snrn/candidate_test.py", line 23, in <module>     assert n`
- task_id=161: 定义 `['remove_elements']` vs 期望 `['remove_elements']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_b010kssa/candidate_test.py", line 7, in <module>     assert re`
- task_id=248: 定义 `['harmonic_sum']` vs 期望 `['harmonic_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_iw1x82ih/candidate_test.py", line 12, in <module>     assert m`

### 类型错误 (type_error)
- task_id=126: 定义 `['find_common_divisors']` vs 期望 `['sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_tw0vw2gl/candidate_test.py", line 11, in <module>     assert s`
- task_id=452: 定义 `['loss_amount']` vs 期望 `['loss_amount']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_0o72v9hi/candidate_test.py", line 10, in <module>     assert l`
- task_id=473: 定义 `['tuple_intersection']` vs 期望 `['tuple_intersection']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_f64au7qr/candidate_test.py", line 12, in <module>     assert t`

### 部分测试通过 (partial_pass)
- task_id=131: 定义 `['reverse_vowels']` vs 期望 `['reverse_vowels']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_9yejlj_2/candidate_test.py", line 14, in <module>     assert r`
- task_id=310: 定义 `['string_to_tuple']` vs 期望 `['string_to_tuple']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_qa1iwbfd/candidate_test.py", line 7, in <module>     assert st`

### 其他运行时错误 (other_runtime)
- task_id=162: 定义 `['sum_of_numbers']` vs 期望 `['sum_series']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_32_o_xnq/candidate_test.py", line 12, in <module>     print(su`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
