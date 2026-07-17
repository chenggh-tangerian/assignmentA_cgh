# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-11T16:27:43.847871+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft_cgh_dataop/outputs_2/eval/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 56，失败 201）
- 部分通过用例: 24
- 全量 pass@1 (metrics): **21.79%**
- 全量语法通过率 (metrics): **94.16%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 86 | 33.5% | 42.8% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 类型错误 | 27 | 10.5% | 13.4% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 部分测试通过 | 23 | 8.9% | 11.4% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 其他运行时错误 | 17 | 6.6% | 8.5% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 语法错误 | 15 | 5.8% | 7.5% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 函数名不匹配 | 14 | 5.5% | 7.0% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 边界条件错误 | 14 | 5.5% | 7.0% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 属性错误 | 4 | 1.6% | 2.0% | 检查是否误用对象属性或 API；补充相关 API 用法示例。 |
| 运行超时 | 1 | 0.4% | 0.5% | 优化算法复杂度相关训练数据；评测可适当放宽 timeout 以区分 TLE vs 逻辑错。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 86 例 (42.8% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P2 类型错误**: 27 例 (13.4% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 部分测试通过**: 23 例 (11.4% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 其他运行时错误**: 17 例 (8.5% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P2 语法错误**: 15 例 (7.5% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P2 函数名不匹配**: 14 例 (7.0% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。

## 典型样例

### 类型错误 (type_error)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "/tmp/mbpp_eval_aj4_r78e/candidate_test.py", line 20, i`
- task_id=65: 定义 `['recursive_list_sum']` vs 期望 `['recursive_list_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_poj2nerf/candidate_test.py", line 13, in <module>     flattene`
- task_id=72: 定义 `['dif_Square']` vs 期望 `['dif_Square']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_fq7ri7df/candidate_test.py", line 19, in <module>     assert d`

### 语法错误 (syntax_error)
- task_id=16: 定义 `['text_lowercase_underscore']` vs 期望 `['text_lowercase_underscore']`
- task_id=56: 定义 `[]` vs 期望 `['check', 'rev']`
- task_id=61: 定义 `[]` vs 期望 `['count_Substrings']`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_cincwipn/candidate_test.py", line 11, in <module>     assert r`
- task_id=64: 定义 `['subject_marks']` vs 期望 `['subject_marks']`
  - stderr: `nce', 90), ('Maths', 97), ('Social sciences', 82)])==[('Social sciences', 82), ('English', 88), ('Science', 90), ('Maths`
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_84s4v_ia/candidate_test.py", line 14, in <module>     assert n`

### 部分测试通过 (partial_pass)
- task_id=20: 定义 `['is_woodall']` vs 期望 `['is_woodall']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_5ymxiwxm/candidate_test.py", line 12, in <module>     assert i`
- task_id=58: 定义 `['opposite_Signs']` vs 期望 `['opposite_Signs']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_nxhpqdvl/candidate_test.py", line 14, in <module>     assert o`
- task_id=68: 定义 `['is_Monotonic']` vs 期望 `['is_Monotonic']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3lt9qvb7/candidate_test.py", line 16, in <module>     assert i`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=57: 定义 `['find_Max_Num']` vs 期望 `['find_Max_Num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_r42sig14/candidate_test.py", line 11, in <module>     assert f`
- task_id=59: 定义 `['is_octagonal']` vs 期望 `['is_octagonal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_enmhrfq4/candidate_test.py", line 17, in <module>     assert i`
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3282lx_c/candidate_test.py", line 21, in <module>     assert m`

### 边界条件错误 (boundary_error)
- task_id=69: 定义 `['is_sublist']` vs 期望 `['is_sublist']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_1ap1rnc6/candidate_test.py", line 13, in <module>     assert i`
- task_id=104: 定义 `['sort_sublists']` vs 期望 `['sort_sublists']`
  - stderr: `py", line 19, in <module>     assert sort_sublists((["green", "orange"], ["black", "white"], ["white", "black", "orange"`
- task_id=106: 定义 `['add_lists']` vs 期望 `['add_lists']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_fqsqsidw/candidate_test.py", line 10, in <module>     assert a`

### 函数名不匹配 (function_name_mismatch)
- task_id=74: 定义 `['is_same_patterns']` vs 期望 `['is_samepatterns']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_v2l32238/candidate_test.py", line 18, in <module>     assert i`
- task_id=84: 定义 `['nth_number_in_newman_coway_sequence', 'find_nth']` vs 期望 `['sequence']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_5mny_zji/candidate_test.py", line 13, in <module>     print(th`
- task_id=244: 定义 `['next']` vs 期望 `['next_Perfect_Square']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_r9nmls43/candidate_test.py", line 15, in <module>     assert n`

### 属性错误 (attribute_error)
- task_id=91: 定义 `['find_substring']` vs 期望 `['find_substring']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_q9mr2b7l/candidate_test.py", line 17, in <module>     assert f`
- task_id=260: 定义 `['newman_prime']` vs 期望 `['newman_prime']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_1u6w5vwh/candidate_test.py", line 18, in <module>     assert n`
- task_id=301: 定义 `['dict_depth']` vs 期望 `['dict_depth']`
  - stderr: `_9j69znws/candidate_test.py", line 11, in <module>     assert dict_depth({'a':1, 'b': {'c': {'d': {}}}})==4            ^`

### 运行超时 (timeout)
- task_id=432: 定义 `['median_trapezium']` vs 期望 `['median_trapezium']`
  - stderr: `Command '['/opt/conda/envs/chenggh-sft/bin/python', '/tmp/mbpp_eval_2etb6n4a/candidate_test.py']' timed out after 5.0 se`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
