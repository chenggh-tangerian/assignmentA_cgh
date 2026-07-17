# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-01T07:51:08.090949+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft/script_cgh/outputs/eval_with_signature/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 63，失败 194）
- 部分通过用例: 38
- 全量 pass@1 (metrics): **24.51%**
- 全量语法通过率 (metrics): **96.11%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 96 | 37.4% | 49.5% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 部分测试通过 | 38 | 14.8% | 19.6% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 类型错误 | 23 | 8.9% | 11.9% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 函数名不匹配 | 13 | 5.1% | 6.7% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 语法错误 | 10 | 3.9% | 5.1% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 其他运行时错误 | 8 | 3.1% | 4.1% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 边界条件错误 | 3 | 1.2% | 1.6% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 属性错误 | 2 | 0.8% | 1.0% | 检查是否误用对象属性或 API；补充相关 API 用法示例。 |
| 运行超时 | 1 | 0.4% | 0.5% | 优化算法复杂度相关训练数据；评测可适当放宽 timeout 以区分 TLE vs 逻辑错。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 96 例 (49.5% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P1 部分测试通过**: 38 例 (19.6% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 类型错误**: 23 例 (11.9% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 函数名不匹配**: 13 例 (6.7% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P2 语法错误**: 10 例 (5.1% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。
- **P3 其他运行时错误**: 8 例 (4.1% 失败) — 人工抽查 stderr，归入更细类别后补充规则。

## 典型样例

### 部分测试通过 (partial_pass)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_0zavrmz2/candidate_test.py", line 19, in <module>     assert s`
- task_id=20: 定义 `['is_woodall']` vs 期望 `['is_woodall']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_42u8yn8g/candidate_test.py", line 10, in <module>     assert i`
- task_id=58: 定义 `['opposite_Signs']` vs 期望 `['opposite_Signs']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3f1w5vb2/candidate_test.py", line 16, in <module>     assert o`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=14: 定义 `['find_Volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3rka0bmo/candidate_test.py", line 7, in <module>     assert fi`
- task_id=71: 定义 `['comb_sort']` vs 期望 `['comb_sort']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_fkcxz3iw/candidate_test.py", line 12, in <module>     assert c`
- task_id=79: 定义 `['word_len']` vs 期望 `['word_len']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_50s847b4/candidate_test.py", line 10, in <module>     assert w`

### 语法错误 (syntax_error)
- task_id=16: 定义 `[]` vs 期望 `['text_lowercase_underscore']`
- task_id=59: 定义 `['is_octagonal']` vs 期望 `['is_octagonal']`
- task_id=61: 定义 `[]` vs 期望 `['count_Substrings']`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_jmkk6zfy/candidate_test.py", line 11, in <module>     assert r`
- task_id=70: 定义 `['find_equal_tuple']` vs 期望 `['find_equal_tuple', 'get_equal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_nz9bqnee/candidate_test.py", line 17, in <module>     assert g`
- task_id=100: 定义 `['next_smallest_palindrome']` vs 期望 `['next_smallest_palindrome']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_tqe83_lf/candidate_test.py", line 18, in <module>     assert n`

### 函数名不匹配 (function_name_mismatch)
- task_id=56: 定义 `['is_one_larger_than_reverse']` vs 期望 `['check', 'rev']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7o5uwakc/candidate_test.py", line 13, in <module>     assert c`
- task_id=57: 定义 `['find']` vs 期望 `['find_Max_Num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rryvxamc/candidate_test.py", line 10, in <module>     assert f`
- task_id=74: 定义 `['is_same_patterns']` vs 期望 `['is_samepatterns']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_vfstinap/candidate_test.py", line 14, in <module>     assert i`

### 类型错误 (type_error)
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_y0mczvzl/candidate_test.py", line 13, in <module>     assert m`
- task_id=64: 定义 `['subject_marks']` vs 期望 `['subject_marks']`
  - stderr: `sert subject_marks([('English', 88), ('Science', 90), ('Maths', 97), ('Social sciences', 82)])==[('Social sciences', 82)`
- task_id=65: 定义 `['recursive_list_sum']` vs 期望 `['recursive_list_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_bijrxodz/candidate_test.py", line 10, in <module>     assert r`

### 边界条件错误 (boundary_error)
- task_id=245: 定义 `['max_sum']` vs 期望 `['max_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_lv5mftx3/candidate_test.py", line 14, in <module>     assert m`
- task_id=307: 定义 `['colon_tuplex']` vs 期望 `['colon_tuplex']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7pxex3c2/candidate_test.py", line 7, in <module>     assert co`
- task_id=470: 定义 `['add_pairwise']` vs 期望 `['add_pairwise']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_wp8962k6/candidate_test.py", line 18, in <module>     assert a`

### 运行超时 (timeout)
- task_id=246: 定义 `['babylonian_squareroot']` vs 期望 `['babylonian_squareroot']`
  - stderr: `Command '['/opt/conda/envs/chenggh-sft/bin/python', '/tmp/mbpp_eval_q5doja08/candidate_test.py']' timed out after 5.0 se`

### 属性错误 (attribute_error)
- task_id=427: 定义 `['change_date_format']` vs 期望 `['change_date_format']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_jdntlami/candidate_test.py", line 7, in <module>     assert ch`
- task_id=437: 定义 `['remove_odd']` vs 期望 `['remove_odd']`
  - stderr: `e_test.py", line 7, in <module>     assert remove_odd("python")==("yhn")            ^^^^^^^^^^^^^^^^^^^^   File "/tmp/mb`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
