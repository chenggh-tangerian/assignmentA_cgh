# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-01T11:48:22.688662+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft/outputs_cgh/eval_sft_with_signature/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 66，失败 191）
- 部分通过用例: 31
- 全量 pass@1 (metrics): **25.68%**
- 全量语法通过率 (metrics): **95.72%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 106 | 41.2% | 55.5% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 部分测试通过 | 30 | 11.7% | 15.7% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 类型错误 | 20 | 7.8% | 10.5% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 语法错误 | 10 | 3.9% | 5.2% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 其他运行时错误 | 10 | 3.9% | 5.2% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 函数名不匹配 | 8 | 3.1% | 4.2% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 边界条件错误 | 5 | 1.9% | 2.6% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 代码截断/重复生成 | 1 | 0.4% | 0.5% | 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。 |
| 属性错误 | 1 | 0.4% | 0.5% | 检查是否误用对象属性或 API；补充相关 API 用法示例。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 106 例 (55.5% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P1 部分测试通过**: 30 例 (15.7% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 类型错误**: 20 例 (10.5% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 语法错误**: 10 例 (5.2% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P2 其他运行时错误**: 10 例 (5.2% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P3 函数名不匹配**: 8 例 (4.2% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。

## 典型样例

### 部分测试通过 (partial_pass)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_0qpoqff1/candidate_test.py", line 11, in <module>     assert s`
- task_id=17: 定义 `['square_perimeter']` vs 期望 `['square_perimeter']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ojn1oqgt/candidate_test.py", line 8, in <module>     assert sq`
- task_id=58: 定义 `['opposite_Signs']` vs 期望 `['opposite_Signs']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_40kgkc7s/candidate_test.py", line 14, in <module>     assert o`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=14: 定义 `['find_Volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3gu3almi/candidate_test.py", line 7, in <module>     assert fi`
- task_id=20: 定义 `['is_woodall']` vs 期望 `['is_woodall']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_csnhabvh/candidate_test.py", line 10, in <module>     assert i`
- task_id=59: 定义 `['is_octagonal']` vs 期望 `['is_octagonal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_zorxkx_u/candidate_test.py", line 17, in <module>     assert i`

### 语法错误 (syntax_error)
- task_id=16: 定义 `[]` vs 期望 `['text_lowercase_underscore']`
- task_id=61: 定义 `[]` vs 期望 `['count_Substrings']`
- task_id=86: 定义 `['centered_hexagonal_number']` vs 期望 `['centered_hexagonal_number']`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rl_7lfjj/candidate_test.py", line 7, in <module>     assert re`
- task_id=56: 定义 `['rev']` vs 期望 `['check', 'rev']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_je5jn27x/candidate_test.py", line 12, in <module>     assert c`
- task_id=67: 定义 `['bell_number']` vs 期望 `['bell_number']`
  - stderr: `) + (n % 2) * bell_number(n + 1)                                                      ^^^^^^^^^^^^^^^^^^   File "/tmp/mb`

### 函数名不匹配 (function_name_mismatch)
- task_id=57: 定义 `['find']` vs 期望 `['find_Max_Num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_be7b9a2d/candidate_test.py", line 11, in <module>     assert f`
- task_id=95: 定义 `['Find_MIN长度']` vs 期望 `['Find_Min_Length']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_w75rkdw7/candidate_test.py", line 12, in <module>     assert F`
- task_id=138: 定义 `['is_Sum_Of_Powers_Of_four']` vs 期望 `['is_Sum_Of_Powers_Of_Two']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7pygtj90/candidate_test.py", line 13, in <module>     assert i`

### 类型错误 (type_error)
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_6qwzqsn_/candidate_test.py", line 12, in <module>     assert m`
- task_id=64: 定义 `['subject_marks']` vs 期望 `['subject_marks']`
  - stderr: `>     assert subject_marks([('English', 88), ('Science', 90), ('Maths', 97), ('Social sciences', 82)])==[('Social scienc`
- task_id=65: 定义 `['recursive_list_sum']` vs 期望 `['recursive_list_sum']`
  - stderr: `  File "/tmp/mbpp_eval_15blrd67/candidate_test.py", line 8, in recursive_list_sum     return data_list[0] + recursive_li`

### 边界条件错误 (boundary_error)
- task_id=91: 定义 `['find_substring']` vs 期望 `['find_substring']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_x6o_0_tk/candidate_test.py", line 11, in <module>     assert f`
- task_id=255: 定义 `['combinations_colors']` vs 期望 `['combinations_colors']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rjf5xrsa/candidate_test.py", line 16, in <module>     assert c`
- task_id=283: 定义 `['validate']` vs 期望 `['validate']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_09pq0xlg/candidate_test.py", line 11, in <module>     assert v`

### 代码截断/重复生成 (truncation_or_repetition)
- task_id=252: 定义 `['convert']` vs 期望 `['convert']`

### 属性错误 (attribute_error)
- task_id=301: 定义 `['dict_depth']` vs 期望 `['dict_depth']`
  - stderr: `tmp/mbpp_eval_nvjceqzu/candidate_test.py", line 14, in <module>     assert dict_depth({'a':1, 'b': {'c': {'d': {}}}})==4`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
