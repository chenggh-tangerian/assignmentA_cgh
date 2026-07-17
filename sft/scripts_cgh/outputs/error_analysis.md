# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-01T07:25:59.230630+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft/outputs/eval_mbpp/mbpp_cases.jsonl`
- 分析样本数: **200**（通过 6，失败 194）
- 部分通过用例: 1
- 全量 pass@1 (metrics): **3.11%**
- 全量语法通过率 (metrics): **95.33%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 函数名不匹配 | 176 | 88.0% | 90.7% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 语法错误 | 7 | 3.5% | 3.6% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 逻辑错误(断言失败) | 5 | 2.5% | 2.6% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 代码截断/重复生成 | 3 | 1.5% | 1.6% | 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。 |
| 类型错误 | 2 | 1.0% | 1.0% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 部分测试通过 | 1 | 0.5% | 0.5% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |

## 优先改进项 (按失败占比)

- **P0 函数名不匹配**: 176 例 (90.7% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P3 语法错误**: 7 例 (3.6% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P3 逻辑错误(断言失败)**: 5 例 (2.6% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P3 代码截断/重复生成**: 3 例 (1.6% 失败) — 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。
- **P3 类型错误**: 2 例 (1.0% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P3 部分测试通过**: 1 例 (0.5% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。

## 典型样例

### 函数名不匹配 (function_name_mismatch)
- task_id=11: 定义 `['remove_first_last_occurrence']` vs 期望 `['remove_Occ']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ua9h1qme/candidate_test.py", line 7, in <module>     assert re`
- task_id=12: 定义 `['sortMatrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_t0y84gpo/candidate_test.py", line 12, in <module>     assert s`
- task_id=14: 定义 `['triangular_prism_volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3jvd3xgc/candidate_test.py", line 7, in <module>     assert fi`

### 代码截断/重复生成 (truncation_or_repetition)
- task_id=17: 定义 `['square_perimeter']` vs 期望 `['square_perimeter']`
- task_id=82: 定义 `['sphere_volume']` vs 期望 `['volume_sphere']`
- task_id=135: 定义 `['hexagon_number']` vs 期望 `['hexagonal_num']`

### 语法错误 (syntax_error)
- task_id=58: 定义 `[]` vs 期望 `['opposite_Signs']`
- task_id=129: 定义 `['isMagicSquare']` vs 期望 `['magic_square_test']`
- task_id=167: 定义 `[]` vs 期望 `['next_power_of_2']`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_qmudfnog/candidate_test.py", line 16, in <module>     assert n`
- task_id=139: 定义 `['circle_circumference']` vs 期望 `['circle_circumference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_yq97s49d/candidate_test.py", line 10, in <module>     assert m`
- task_id=161: 定义 `['remove_elements']` vs 期望 `['remove_elements']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ooiw7fmh/candidate_test.py", line 12, in <module>     assert r`

### 类型错误 (type_error)
- task_id=126: 定义 `['findCommonDivisors']` vs 期望 `['sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_opcz3k7j/candidate_test.py", line 12, in <module>     assert s`
- task_id=131: 定义 `['reverse_vowels']` vs 期望 `['reverse_vowels']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_jfvzvtki/candidate_test.py", line 12, in <module>     assert r`

### 部分测试通过 (partial_pass)
- task_id=310: 定义 `['string_to_tuple']` vs 期望 `['string_to_tuple']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_plrr16kf/candidate_test.py", line 7, in <module>     assert st`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
