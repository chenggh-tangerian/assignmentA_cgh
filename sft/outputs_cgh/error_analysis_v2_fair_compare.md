# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-02T02:18:04.784581+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft/outputs_cgh/eval_v2_fair_compare/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 2，失败 255）
- 部分通过用例: 2
- 全量 pass@1 (metrics): **0.78%**
- 全量语法通过率 (metrics): **93.39%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 函数名不匹配 | 214 | 83.3% | 83.9% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 语法错误 | 15 | 5.8% | 5.9% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 类型错误 | 10 | 3.9% | 3.9% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 逻辑错误(断言失败) | 7 | 2.7% | 2.8% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 其他运行时错误 | 4 | 1.6% | 1.6% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 代码截断/重复生成 | 2 | 0.8% | 0.8% | 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。 |
| 边界条件错误 | 1 | 0.4% | 0.4% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 运行超时 | 1 | 0.4% | 0.4% | 优化算法复杂度相关训练数据；评测可适当放宽 timeout 以区分 TLE vs 逻辑错。 |
| 部分测试通过 | 1 | 0.4% | 0.4% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |

## 优先改进项 (按失败占比)

- **P0 函数名不匹配**: 214 例 (83.9% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P2 语法错误**: 15 例 (5.9% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P3 类型错误**: 10 例 (3.9% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P3 逻辑错误(断言失败)**: 7 例 (2.8% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P3 其他运行时错误**: 4 例 (1.6% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P3 代码截断/重复生成**: 2 例 (0.8% 失败) — 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。

## 典型样例

### 函数名不匹配 (function_name_mismatch)
- task_id=11: 定义 `['remove_first_last_char']` vs 期望 `['remove_Occ']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_wflprkah/candidate_test.py", line 11, in <module>     assert r`
- task_id=12: 定义 `['sortMatrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval__7mqde6v/candidate_test.py", line 23, in <module>     assert s`
- task_id=16: 定义 `['contains_sequences_lowercase']` vs 期望 `['text_lowercase_underscore']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_gth0oyqb/candidate_test.py", line 7, in <module>     assert te`

### 语法错误 (syntax_error)
- task_id=14: 定义 `[]` vs 期望 `['find_Volume']`
- task_id=58: 定义 `[]` vs 期望 `['opposite_Signs']`
- task_id=72: 定义 `[]` vs 期望 `['dif_Square']`

### 类型错误 (type_error)
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_bndocdv_/candidate_test.py", line 12, in <module>     assert m`
- task_id=67: 定义 `['num_ways']` vs 期望 `['bell_number']`
  - stderr: `ays(bell_nums))           ^^^^^^^^^^^^^^^^^^^   File "/tmp/mbpp_eval_9_95bote/candidate_test.py", line 11, in num_ways  `
- task_id=85: 定义 `['surface_area']` vs 期望 `['surfacearea_sphere']`
  - stderr: `(most recent call last):   File "/tmp/mbpp_eval_7o2p8r8b/candidate_test.py", line 18, in <module>     print("Surface Are`

### 运行超时 (timeout)
- task_id=86: 定义 `['nthCentricHexagonalNumber']` vs 期望 `['centered_hexagonal_number']`
  - stderr: `Command '['/opt/conda/envs/chenggh-sft/bin/python', '/tmp/mbpp_eval_0htbh36u/candidate_test.py']' timed out after 5.0 se`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_vvz8eis5/candidate_test.py", line 20, in <module>     assert n`
- task_id=131: 定义 `['reverse_vowels']` vs 期望 `['reverse_vowels']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_oug4az38/candidate_test.py", line 12, in <module>     assert r`
- task_id=161: 定义 `['remove_elements']` vs 期望 `['remove_elements']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ozii45g0/candidate_test.py", line 11, in <module>     assert r`

### 其他运行时错误 (other_runtime)
- task_id=108: 定义 `['merge_sort']` vs 期望 `['merge_sorted_list']`
  - stderr: `, list3)                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/tmp/mbpp_eval_h9og0hp4/candidate_test.py", line 14, `
- task_id=264: 定义 `[]` vs 期望 `['dog_age']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7mrcn7jd/candidate_test.py", line 7, in <module>     age = int`
- task_id=397: 定义 `[]` vs 期望 `['median_numbers']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_6xfxqd28/candidate_test.py", line 7, in <module>     num1 = in`

### 代码截断/重复生成 (truncation_or_repetition)
- task_id=300: 定义 `[]` vs 期望 `['count_binary_seq']`
- task_id=389: 定义 `['lucas_number']` vs 期望 `['find_lucas']`

### 部分测试通过 (partial_pass)
- task_id=310: 定义 `['string_to_tuple']` vs 期望 `['string_to_tuple']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_m0urxqlm/candidate_test.py", line 7, in <module>     assert st`

### 边界条件错误 (boundary_error)
- task_id=427: 定义 `[]` vs 期望 `['change_date_format']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rwc98u6k/candidate_test.py", line 13, in <module>     date = d`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
