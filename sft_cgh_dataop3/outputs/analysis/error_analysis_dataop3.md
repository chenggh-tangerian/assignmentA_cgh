# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-12T06:49:49.454942+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft_cgh_dataop3/outputs/eval/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 61，失败 196）
- 部分通过用例: 33
- 全量 pass@1 (metrics): **23.74%**
- 全量语法通过率 (metrics): **96.50%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 98 | 38.1% | 50.0% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 部分测试通过 | 32 | 12.4% | 16.3% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 类型错误 | 27 | 10.5% | 13.8% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 其他运行时错误 | 12 | 4.7% | 6.1% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 函数名不匹配 | 10 | 3.9% | 5.1% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 语法错误 | 8 | 3.1% | 4.1% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 属性错误 | 4 | 1.6% | 2.0% | 检查是否误用对象属性或 API；补充相关 API 用法示例。 |
| 边界条件错误 | 3 | 1.2% | 1.5% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 代码截断/重复生成 | 1 | 0.4% | 0.5% | 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。 |
| 运行超时 | 1 | 0.4% | 0.5% | 优化算法复杂度相关训练数据；评测可适当放宽 timeout 以区分 TLE vs 逻辑错。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 98 例 (50.0% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P1 部分测试通过**: 32 例 (16.3% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 类型错误**: 27 例 (13.8% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 其他运行时错误**: 12 例 (6.1% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P2 函数名不匹配**: 10 例 (5.1% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P3 语法错误**: 8 例 (4.1% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。

## 典型样例

### 逻辑错误(断言失败) (assertion_failure)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_g1akzra2/candidate_test.py", line 13, in <module>     assert s`
- task_id=14: 定义 `['find_Volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_4k3wxz31/candidate_test.py", line 10, in <module>     assert f`
- task_id=17: 定义 `['square_perimeter']` vs 期望 `['square_perimeter']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7ftrrb3z/candidate_test.py", line 8, in <module>     assert sq`

### 部分测试通过 (partial_pass)
- task_id=16: 定义 `['text_lowercase_underscore']` vs 期望 `['text_lowercase_underscore']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_76fjjf_k/candidate_test.py", line 7, in <module>     assert te`
- task_id=58: 定义 `['opposite_Signs']` vs 期望 `['opposite_Signs']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_0q2k14o3/candidate_test.py", line 16, in <module>     assert o`
- task_id=67: 定义 `['bell_number']` vs 期望 `['bell_number']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_hsvb98wh/candidate_test.py", line 14, in <module>     assert b`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_gylijual/candidate_test.py", line 7, in <module>     assert re`
- task_id=56: 定义 `['rev', 'is_one_less_than_reverse']` vs 期望 `['check', 'rev']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_zu7p_d48/candidate_test.py", line 12, in <module>     assert c`
- task_id=70: 定义 `['find_equal_tuple']` vs 期望 `['find_equal_tuple', 'get_equal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_h3gxs5r8/candidate_test.py", line 10, in <module>     assert g`

### 函数名不匹配 (function_name_mismatch)
- task_id=57: 定义 `['find']` vs 期望 `['find_Max_Num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_e4nklbxw/candidate_test.py", line 11, in <module>     assert f`
- task_id=61: 定义 `['count']` vs 期望 `['count_Substrings']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_gfpri1sh/candidate_test.py", line 13, in <module>     assert c`
- task_id=74: 定义 `['is_same_patterns']` vs 期望 `['is_samepatterns']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_77gose2u/candidate_test.py", line 11, in <module>     assert i`

### 类型错误 (type_error)
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_wfjij54_/candidate_test.py", line 13, in <module>     assert m`
- task_id=65: 定义 `['recursive_list_sum', 'sum_list_elements']` vs 期望 `['recursive_list_sum']`
  - stderr: `  File "/tmp/mbpp_eval_9hrjd93t/candidate_test.py", line 8, in recursive_list_sum     return data_list[0] + recursive_li`
- task_id=75: 定义 `['find_tuples']` vs 期望 `['find_tuples']`
  - stderr: `aceback (most recent call last):   File "/tmp/mbpp_eval__rsp0t2y/candidate_test.py", line 13, in <module>     assert fin`

### 边界条件错误 (boundary_error)
- task_id=64: 定义 `['subject_marks']` vs 期望 `['subject_marks']`
  - stderr: `n <module>     assert subject_marks([('English', 88), ('Science', 90), ('Maths', 97), ('Social sciences', 82)])==[('Soci`
- task_id=119: 定义 `['search']` vs 期望 `['search']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7dn7nt68/candidate_test.py", line 12, in <module>     assert s`
- task_id=124: 定义 `['angle_complex']` vs 期望 `['angle_complex']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_uhmgk3i_/candidate_test.py", line 15, in <module>     print(an`

### 语法错误 (syntax_error)
- task_id=83: 定义 `['get_Char']` vs 期望 `['get_Char']`
- task_id=95: 定义 `[]` vs 期望 `['Find_Min_Length']`
- task_id=108: 定义 `['merge_sorted_list']` vs 期望 `['merge_sorted_list']`

### 代码截断/重复生成 (truncation_or_repetition)
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`

### 属性错误 (attribute_error)
- task_id=130: 定义 `['max_occurrences']` vs 期望 `['max_occurrences']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_5p4va6zt/candidate_test.py", line 14, in <module>     assert m`
- task_id=308: 定义 `['large_product']` vs 期望 `['large_product']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rm4z121s/candidate_test.py", line 10, in <module>     assert l`
- task_id=437: 定义 `['remove_odd']` vs 期望 `['remove_odd']`
  - stderr: `.py", line 8, in <module>     assert remove_odd("python")==("yhn")            ^^^^^^^^^^^^^^^^^^^^   File "/tmp/mbpp_eva`

### 运行超时 (timeout)
- task_id=389: 定义 `['find_lucas']` vs 期望 `['find_lucas']`
  - stderr: `Command '['/opt/conda/envs/chenggh-sft/bin/python', '/tmp/mbpp_eval_rscwcsn7/candidate_test.py']' timed out after 5.0 se`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
