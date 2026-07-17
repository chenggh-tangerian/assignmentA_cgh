# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-11T15:05:32.991236+00:00
- 数据来源: `/root/siton-tmp/assignment_A/sft_cgh_dataop/outputs/eval/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 57，失败 200）
- 部分通过用例: 26
- 全量 pass@1 (metrics): **22.18%**
- 全量语法通过率 (metrics): **97.28%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 108 | 42.0% | 54.0% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 部分测试通过 | 25 | 9.7% | 12.5% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 函数名不匹配 | 19 | 7.4% | 9.5% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 类型错误 | 18 | 7.0% | 9.0% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 其他运行时错误 | 14 | 5.5% | 7.0% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 边界条件错误 | 9 | 3.5% | 4.5% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 语法错误 | 7 | 2.7% | 3.5% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 108 例 (54.0% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P2 部分测试通过**: 25 例 (12.5% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 函数名不匹配**: 19 例 (9.5% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P2 类型错误**: 18 例 (9.0% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 其他运行时错误**: 14 例 (7.0% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P3 边界条件错误**: 9 例 (4.5% 失败) — 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。

## 典型样例

### 逻辑错误(断言失败) (assertion_failure)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_zdx6em8l/candidate_test.py", line 24, in <module>     assert s`
- task_id=14: 定义 `['find_Volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_7nfha3xj/candidate_test.py", line 9, in <module>     assert fi`
- task_id=20: 定义 `['is_woodall']` vs 期望 `['is_woodall']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_gp0npno1/candidate_test.py", line 12, in <module>     assert i`

### 部分测试通过 (partial_pass)
- task_id=16: 定义 `['text_lowercase_underscore']` vs 期望 `['text_lowercase_underscore']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_jz6o8gws/candidate_test.py", line 8, in <module>     assert te`
- task_id=58: 定义 `['opposite_Signs']` vs 期望 `['opposite_Signs']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_snv3gjc1/candidate_test.py", line 19, in <module>     assert o`
- task_id=67: 定义 `['bell_number']` vs 期望 `['bell_number']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_lrkgyksa/candidate_test.py", line 14, in <module>     assert b`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_bg3wbnlp/candidate_test.py", line 12, in <module>     assert r`
- task_id=64: 定义 `['subject_marks']` vs 期望 `['subject_marks']`
  - stderr: `ine 10, in <module>     assert subject_marks([('English', 88), ('Science', 90), ('Maths', 97), ('Social sciences', 82)])`
- task_id=70: 定义 `['find_equal_tuple']` vs 期望 `['find_equal_tuple', 'get_equal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_t4ma3aiv/candidate_test.py", line 14, in <module>     assert g`

### 语法错误 (syntax_error)
- task_id=56: 定义 `[]` vs 期望 `['check', 'rev']`
- task_id=138: 定义 `[]` vs 期望 `['is_Sum_Of_Powers_Of_Two']`
- task_id=252: 定义 `['convert']` vs 期望 `['convert']`

### 函数名不匹配 (function_name_mismatch)
- task_id=61: 定义 `['count']` vs 期望 `['count_Substrings']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_f1i6dad9/candidate_test.py", line 15, in <module>     assert c`
- task_id=74: 定义 `['is_same_patterns']` vs 期望 `['is_samepatterns']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_3ackjejj/candidate_test.py", line 37, in <module>     assert i`
- task_id=84: 定义 `['nth_number']` vs 期望 `['sequence']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_t__xhnjl/candidate_test.py", line 25, in <module>     assert s`

### 类型错误 (type_error)
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_10ds372l/candidate_test.py", line 12, in <module>     assert m`
- task_id=65: 定义 `['recursive_list_sum']` vs 期望 `['recursive_list_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_ywf4jc5z/candidate_test.py", line 11, in <module>     assert r`
- task_id=89: 定义 `['closest_num']` vs 期望 `['closest_num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_cf6ye2fa/candidate_test.py", line 13, in <module>     assert c`

### 边界条件错误 (boundary_error)
- task_id=106: 定义 `['add_lists']` vs 期望 `['add_lists']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_acfzaqpm/candidate_test.py", line 11, in <module>     assert a`
- task_id=240: 定义 `['replace_list']` vs 期望 `['replace_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_qub2k59w/candidate_test.py", line 10, in <module>     assert r`
- task_id=245: 定义 `['max_sum']` vs 期望 `['max_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_emctg1w_/candidate_test.py", line 31, in <module>     assert m`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
