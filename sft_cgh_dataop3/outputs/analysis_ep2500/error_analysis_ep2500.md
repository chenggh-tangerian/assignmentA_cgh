# 代码任务错误分析报告

- 生成时间(UTC): 2026-07-13T04:13:42.290884+00:00
- 数据来源: `sft_cgh_dataop3/outputs/eval_ep2500/mbpp_cases.jsonl`
- 分析样本数: **257**（通过 58，失败 199）
- 部分通过用例: 29
- 全量 pass@1 (metrics): **22.57%**
- 全量语法通过率 (metrics): **96.11%**

> Cases file may be a subset (evaluate_code_predictions.py default case_limit=200). Compare num_cases_analyzed with metrics num_tasks for coverage.

## 错误类型分布

| 类型 | 数量 | 占全部 | 占失败 | 改进建议 |
|------|------|--------|--------|----------|
| 逻辑错误(断言失败) | 113 | 44.0% | 56.8% | 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。 |
| 部分测试通过 | 28 | 10.9% | 14.1% | 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。 |
| 类型错误 | 24 | 9.3% | 12.1% | 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。 |
| 函数名不匹配 | 10 | 3.9% | 5.0% | 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好... |
| 其他运行时错误 | 9 | 3.5% | 4.5% | 人工抽查 stderr，归入更细类别后补充规则。 |
| 语法错误 | 7 | 2.7% | 3.5% | 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。 |
| 边界条件错误 | 4 | 1.6% | 2.0% | 针对空输入、单元素、越界等边界构造专项训练样本；可用 hard negative 做 DPO。 |
| 代码截断/重复生成 | 3 | 1.2% | 1.5% | 增大 max_new_tokens；加入截断惩罚或重复惩罚；SFT 数据避免过长重复模式。 |
| 属性错误 | 1 | 0.4% | 0.5% | 检查是否误用对象属性或 API；补充相关 API 用法示例。 |

## 优先改进项 (按失败占比)

- **P0 逻辑错误(断言失败)**: 113 例 (56.8% 失败) — 核心逻辑错误：增加相似算法题解、分步推理数据，或做 execution-based 微调/DPO。
- **P2 部分测试通过**: 28 例 (14.1% 失败) — 分析未通过的 assert 模式，针对失败用例做 targeted 数据增强。
- **P2 类型错误**: 24 例 (12.1% 失败) — 增加类型边界样例（空列表、None、混合类型）；加强 docstring/参数说明。
- **P2 函数名不匹配**: 10 例 (5.0% 失败) — 训练数据与评测对齐函数命名（MBPP 要求与题目一致）；prompt 中显式给出函数签名；DPO 可用「错名/对名」偏好对。
- **P3 其他运行时错误**: 9 例 (4.5% 失败) — 人工抽查 stderr，归入更细类别后补充规则。
- **P3 语法错误**: 7 例 (3.5% 失败) — 增加语法正确的代码样本；训练时强调完整函数体与闭合括号；检查 max_new_tokens 是否过小。

## 典型样例

### 类型错误 (type_error)
- task_id=12: 定义 `['sort_matrix']` vs 期望 `['sort_matrix']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_f5ukryxx/candidate_test.py", line 18, in <module>     assert s`
- task_id=63: 定义 `['max_difference']` vs 期望 `['max_difference']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_w8lelzxa/candidate_test.py", line 13, in <module>     assert m`
- task_id=84: 定义 `['sequence']` vs 期望 `['sequence']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_0i6slyqn/candidate_test.py", line 18, in <module>     assert s`

### 逻辑错误(断言失败) (assertion_failure)
- task_id=14: 定义 `['find_Volume']` vs 期望 `['find_Volume']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_1_u4rl68/candidate_test.py", line 10, in <module>     assert f`
- task_id=59: 定义 `['is_octagonal']` vs 期望 `['is_octagonal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_8saitgdy/candidate_test.py", line 17, in <module>     assert i`
- task_id=65: 定义 `['recursive_list_sum']` vs 期望 `['recursive_list_sum']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_oux7lzcl/candidate_test.py", line 10, in <module>     assert r`

### 语法错误 (syntax_error)
- task_id=16: 定义 `['text_lowercase_underscore']` vs 期望 `['text_lowercase_underscore']`
- task_id=61: 定义 `[]` vs 期望 `['count_Substrings']`
- task_id=102: 定义 `['snake_to_camel']` vs 期望 `['snake_to_camel']`

### 部分测试通过 (partial_pass)
- task_id=17: 定义 `['square_perimeter']` vs 期望 `['square_perimeter']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_op9ytiii/candidate_test.py", line 10, in <module>     assert s`
- task_id=19: 定义 `['test_duplicate']` vs 期望 `['test_duplicate']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_oyqawezw/candidate_test.py", line 10, in <module>     assert t`
- task_id=20: 定义 `['is_woodall']` vs 期望 `['is_woodall']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_inyt2xk7/candidate_test.py", line 12, in <module>     assert i`

### 其他运行时错误 (other_runtime)
- task_id=18: 定义 `['str_to_list']` vs 期望 `['get_char_count_array', 'lst_to_string', 'remove_dirty_chars', 'str_to_list']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_v2qr8u2_/candidate_test.py", line 7, in <module>     assert re`
- task_id=56: 定义 `['rev']` vs 期望 `['check', 'rev']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_143g1n93/candidate_test.py", line 9, in <module>     assert ch`
- task_id=70: 定义 `['find_equal_tuple']` vs 期望 `['find_equal_tuple', 'get_equal']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_oethg8td/candidate_test.py", line 10, in <module>     assert g`

### 函数名不匹配 (function_name_mismatch)
- task_id=57: 定义 `['find']` vs 期望 `['find_Max_Num']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_qe3wsx9f/candidate_test.py", line 11, in <module>     assert f`
- task_id=74: 定义 `['is_same_patterns']` vs 期望 `['is_samepatterns']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_asvex9rp/candidate_test.py", line 10, in <module>     assert i`
- task_id=95: 定义 `['Find_Min长度']` vs 期望 `['Find_Min_Length']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_w_v5_i35/candidate_test.py", line 11, in <module>     assert F`

### 代码截断/重复生成 (truncation_or_repetition)
- task_id=67: 定义 `['bell_number']` vs 期望 `['bell_number']`
- task_id=233: 定义 `['lateralsuface_cylinder']` vs 期望 `['lateralsuface_cylinder']`
- task_id=293: 定义 `['otherside_rightangle']` vs 期望 `['otherside_rightangle']`

### 边界条件错误 (boundary_error)
- task_id=124: 定义 `['angle_complex']` vs 期望 `['angle_complex']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_2a8vzhx8/candidate_test.py", line 13, in <module>     print(an`
- task_id=129: 定义 `['magic_square_test']` vs 期望 `['magic_square_test']`
  - stderr: `ack (most recent call last):   File "/tmp/mbpp_eval_atyl_g6t/candidate_test.py", line 19, in <module>     assert magic_s`
- task_id=283: 定义 `['validate']` vs 期望 `['validate']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_vf0o3igm/candidate_test.py", line 11, in <module>     assert v`

### 属性错误 (attribute_error)
- task_id=427: 定义 `['change_date_format']` vs 期望 `['change_date_format']`
  - stderr: `Traceback (most recent call last):   File "/tmp/mbpp_eval_rrrahpv5/candidate_test.py", line 9, in <module>     assert ch`

## 如何据此提升准确率

1. **先看 P0/P1**：失败占比最高的类别决定首轮数据/训练改动。
2. **函数名不匹配**：通常是「会做但名字不对」，优先修 prompt 与 SFT 命名规范，性价比高。
3. **断言失败**：真正逻辑错误，需要更多同类题解或 execution-based DPO。
4. **语法/截断**：检查 `max_new_tokens`、停止符，并过滤训练集里的不完整代码。
5. **对比实验**：每次改动后重新 predict + evaluate，再跑本分析脚本，对比 category 分布是否下降。
