# a5_cgh/scripts

根目录执行：`cd /root/siton-tmp/assignment_A`  
Test-Time 评测：Greedy / CoT / ToT。

| 脚本 | 功能 | 运行 |
|------|------|------|
| `eval_greedy.sh` | 贪心解码 MBPP 评测 | `LIMIT=2 bash a5_cgh/scripts/eval_greedy.sh` |
| `eval_cot.sh` | CoT 结构化 Prompt 评测 | `LIMIT=2 bash a5_cgh/scripts/eval_cot.sh` |
| `eval_tot.sh` | Tree-of-Thoughts 评测 | `LIMIT=2 bash a5_cgh/scripts/eval_tot.sh` |
| `build_tot_tree_html.py` | ToT 搜索树可视化 HTML | `python a5_cgh/scripts/build_tot_tree_html.py` |

全量：去掉 `LIMIT`。换模型：`MODEL_PATH=... bash a5_cgh/scripts/eval_*.sh`  
仅重评：`SKIP_GENERATION=1 bash a5_cgh/scripts/eval_greedy.sh`
