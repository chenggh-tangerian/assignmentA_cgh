#!/usr/bin/env python3
"""从 mbpp_tot_records.jsonl 生成可浏览的 ToT 搜索树 HTML。

输入
----
- a5_cgh/outputs/eval_tot/mbpp_tot_records.jsonl
  （或 --records 指定路径）

输出
----
- a5_cgh/outputs/eval_tot/tot_search_trees.html   离线可打开的查看器
- a5_cgh/outputs/eval_tot/tot_trees_compact.json  精简树数据（可选调试）

Usage:
  python a5_cgh/scripts/build_tot_tree_html.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


A5_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = A5_ROOT / "outputs" / "eval_tot" / "mbpp_tot_records.jsonl"
DEFAULT_HTML = A5_ROOT / "outputs" / "eval_tot" / "tot_search_trees.html"
DEFAULT_COMPACT = A5_ROOT / "outputs" / "eval_tot" / "tot_trees_compact.json"


def parse_args() -> argparse.Namespace:
    """解析生成器 CLI。"""
    p = argparse.ArgumentParser(description="Build ToT search tree HTML viewer")
    p.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    p.add_argument("--html", type=Path, default=DEFAULT_HTML)
    p.add_argument("--compact_json", type=Path, default=DEFAULT_COMPACT)
    p.add_argument("--thought_chars", type=int, default=1200)
    p.add_argument("--code_chars", type=int, default=2000)
    p.add_argument("--prompt_chars", type=int, default=500)
    return p.parse_args()


def compact_record(row: dict, *, thought_chars: int, code_chars: int, prompt_chars: int) -> dict:
    """把一条 ToT record 压成查看器所需的精简树。"""
    selected_id = (row.get("selected") or {}).get("node_id")
    kept = set(row.get("kept_thought_ids") or [])
    cand_by_id = {c.get("node_id"): c for c in (row.get("code_candidates") or [])}

    thoughts, codes = [], []
    for n in row.get("nodes") or []:
        if n.get("phase") == "thought":
            thoughts.append(
                {
                    "id": n.get("node_id"),
                    "value": n.get("value_score"),
                    "kept": n.get("node_id") in kept,
                    "thought": (n.get("thought") or "")[:thought_chars],
                    "tokens": n.get("total_tokens"),
                }
            )
        elif n.get("phase") == "code":
            c = cand_by_id.get(n.get("node_id"), {})
            codes.append(
                {
                    "id": n.get("node_id"),
                    "parent": n.get("parent_id"),
                    "code": (c.get("code") or n.get("code") or "")[:code_chars],
                    "passed": bool(c.get("passed", False)),
                    "syntax_ok": bool(c.get("syntax_ok", False)),
                    "passed_tests": c.get("passed_tests"),
                    "total_tests": c.get("total_tests"),
                    "verifier": c.get("verifier_score"),
                    "selected": n.get("node_id") == selected_id,
                    "tokens": n.get("total_tokens"),
                }
            )

    ts = row.get("token_stats") or {}
    return {
        "task_id": row.get("task_id"),
        "passed": bool(row.get("passed")),
        "prompt": (row.get("prompt") or "")[:prompt_chars],
        "num_thoughts": row.get("num_thoughts"),
        "num_kept": row.get("num_kept_thoughts"),
        "num_code": row.get("num_code_candidates"),
        "selected_id": selected_id,
        "tokens": ts.get("total_tokens"),
        "thoughts": thoughts,
        "codes": codes,
    }


def build_html(tasks: list[dict]) -> str:
    """嵌入 TASKS JSON，生成单文件离线 HTML。"""
    data_js = json.dumps(tasks, ensure_ascii=False, separators=(",", ":"))
    # HTML/JS template uses {{{DATA}}} placeholder
    template = Path(__file__).with_name("_tot_tree_viewer_template.html")
    if template.exists():
        return template.read_text(encoding="utf-8").replace("{{{DATA}}}", data_js)

    # fallback: inline minimal template (same viewer as generated below)
    return _DEFAULT_TEMPLATE.replace("{{{DATA}}}", data_js)


_DEFAULT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ToT Search Tree Viewer — MBPP</title>
<style>
:root {
  --bg: #0f1419; --surface: #1a2332; --surface2: #243044; --border: #2d3a4f;
  --text: #e7ecf3; --muted: #8b9cb3; --accent: #3b82f6;
  --green: #22c55e; --red: #ef4444;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column;
}
header {
  padding: 0.85rem 1.25rem; border-bottom: 1px solid var(--border);
  display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; background: var(--surface);
}
header h1 { font-size: 1.05rem; margin: 0; font-weight: 650; }
.badge {
  font-size: 0.75rem; padding: 0.2rem 0.55rem; border-radius: 999px;
  border: 1px solid var(--border); color: var(--muted);
}
.badge.ok { color: #86efac; border-color: #16a34a55; background: #14532d33; }
.badge.fail { color: #fca5a5; border-color: #dc262655; background: #7f1d1d33; }
.toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-left: auto; }
input, select, button {
  background: var(--surface2); color: var(--text); border: 1px solid var(--border);
  border-radius: 8px; padding: 0.4rem 0.65rem; font-size: 0.85rem;
}
input[type="search"] { min-width: 180px; }
button { cursor: pointer; }
button:hover { border-color: var(--accent); }
main { flex: 1; display: grid; grid-template-columns: 280px 1fr; min-height: 0; }
#list { border-right: 1px solid var(--border); overflow: auto; background: #121820; }
.item {
  padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--border);
  cursor: pointer; display: grid; gap: 0.25rem;
}
.item:hover { background: #ffffff08; }
.item.active { background: #1e3a5f55; border-left: 3px solid var(--accent); }
.item .row1 { display: flex; justify-content: space-between; gap: 0.5rem; align-items: center; }
.item .tid { font-weight: 650; font-variant-numeric: tabular-nums; }
.item .meta { font-size: 0.75rem; color: var(--muted); }
#detail { overflow: auto; padding: 1rem 1.25rem 2rem; }
.section { margin-bottom: 1.25rem; }
.section h2 {
  font-size: 0.95rem; margin: 0 0 0.6rem; color: #cbd5e1;
  border-bottom: 1px solid var(--border); padding-bottom: 0.35rem;
}
.prompt, .mono {
  white-space: pre-wrap; word-break: break-word;
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: 0.8rem; background: #0d1117; border: 1px solid var(--border);
  border-radius: 10px; padding: 0.85rem 1rem; line-height: 1.5; color: #d1d9e6;
}
.tree { display: flex; flex-direction: column; gap: 0.75rem; }
.thought {
  border: 1px solid var(--border); border-radius: 12px; background: var(--surface); overflow: hidden;
}
.thought.kept { border-color: #2563eb88; }
.thought.pruned { opacity: 0.55; }
.thought-head {
  padding: 0.65rem 0.9rem; display: flex; flex-wrap: wrap; gap: 0.5rem;
  align-items: center; background: var(--surface2); cursor: pointer;
}
.thought-body { padding: 0.75rem 0.9rem; display: none; border-top: 1px solid var(--border); }
.thought.open .thought-body { display: block; }
.codes { display: grid; gap: 0.55rem; margin-top: 0.65rem; }
.code {
  border: 1px solid var(--border); border-radius: 10px; background: #0d1117; padding: 0.65rem 0.8rem;
}
.code.selected { border-color: #22c55e99; box-shadow: 0 0 0 1px #22c55e44; }
.code-head { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; margin-bottom: 0.45rem; }
.tag {
  font-size: 0.7rem; padding: 0.12rem 0.45rem; border-radius: 999px;
  border: 1px solid var(--border); color: var(--muted);
}
.tag.kept { color: #93c5fd; border-color: #2563eb66; }
.tag.pruned { color: #9ca3af; }
.tag.pass { color: #86efac; border-color: #16a34a66; }
.tag.fail { color: #fca5a5; border-color: #dc262666; }
.tag.selected { color: #86efac; background: #14532d55; border-color: #22c55e88; }
.stats { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 0.5rem 0 1rem; }
.stat {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 0.55rem 0.75rem; min-width: 100px;
}
.stat .l { font-size: 0.72rem; color: var(--muted); }
.stat .v { font-size: 1.1rem; font-weight: 700; margin-top: 0.1rem; }
.empty { color: var(--muted); padding: 2rem; text-align: center; }
.legend { font-size: 0.75rem; color: var(--muted); }
@media (max-width: 860px) {
  main { grid-template-columns: 1fr; }
  #list { max-height: 28vh; border-right: none; border-bottom: 1px solid var(--border); }
}
</style>
</head>
<body>
<header>
  <h1>ToT Search Tree Viewer</h1>
  <span class="badge" id="summary">loading…</span>
  <div class="toolbar">
    <input id="q" type="search" placeholder="搜索 task_id / 题目关键词" />
    <select id="filter">
      <option value="all">全部题目</option>
      <option value="pass">仅通过</option>
      <option value="fail">仅失败</option>
    </select>
    <button type="button" id="expandAll">展开计划</button>
    <button type="button" id="collapseAll">收起计划</button>
  </div>
</header>
<main>
  <aside id="list"></aside>
  <section id="detail"><div class="empty">从左侧选择一道题查看搜索树</div></section>
</main>
<script>
const TASKS = {{{DATA}}};
let filtered = TASKS.slice();
let currentId = null;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderList() {
  const el = document.getElementById('list');
  if (!filtered.length) {
    el.innerHTML = '<div class="empty">无匹配题目</div>';
    return;
  }
  el.innerHTML = filtered.map(t => `
    <div class="item ${t.task_id===currentId?'active':''}" data-id="${t.task_id}">
      <div class="row1">
        <span class="tid">#${t.task_id}</span>
        <span class="badge ${t.passed?'ok':'fail'}">${t.passed?'PASS':'FAIL'}</span>
      </div>
      <div class="meta">thought ${t.num_thoughts} → keep ${t.num_kept} → code ${t.num_code} · ${t.tokens ?? 0} tok</div>
      <div class="meta">${esc((t.prompt||'').slice(0,70))}${(t.prompt||'').length>70?'…':''}</div>
    </div>`).join('');
  el.querySelectorAll('.item').forEach(node => {
    node.addEventListener('click', () => selectTask(Number(node.dataset.id)));
  });
}

function applyFilter() {
  const mode = document.getElementById('filter').value;
  const q = document.getElementById('q').value.trim().toLowerCase();
  filtered = TASKS.filter(t => {
    if (mode === 'pass' && !t.passed) return false;
    if (mode === 'fail' && t.passed) return false;
    if (!q) return true;
    if (String(t.task_id).includes(q)) return true;
    return (t.prompt || '').toLowerCase().includes(q);
  });
  renderList();
  document.getElementById('summary').textContent =
    `显示 ${filtered.length} / ${TASKS.length} · 全量通过 ${TASKS.filter(t=>t.passed).length}`;
}

function codeBlock(c) {
  return `
    <div class="code ${c.selected?'selected':''}">
      <div class="code-head">
        <span class="tag">${esc(c.id)}</span>
        ${c.selected?'<span class="tag selected">SELECTED</span>':''}
        <span class="tag ${c.passed?'pass':'fail'}">${c.passed?'tests PASS':'tests FAIL'}</span>
        <span class="tag ${c.syntax_ok?'pass':'fail'}">syntax ${c.syntax_ok?'OK':'BAD'}</span>
        <span class="tag">tests ${c.passed_tests ?? '?'}/${c.total_tests ?? '?'}</span>
        <span class="tag">verifier ${c.verifier ?? '?'}</span>
        <span class="tag">${c.tokens ?? 0} tok</span>
      </div>
      <div class="mono">${esc(c.code || '(empty code)')}</div>
    </div>`;
}

function selectTask(taskId) {
  currentId = taskId;
  renderList();
  const t = TASKS.find(x => x.task_id === taskId);
  const detail = document.getElementById('detail');
  if (!t) {
    detail.innerHTML = '<div class="empty">未找到</div>';
    return;
  }
  const codesByParent = {};
  (t.codes || []).forEach(c => {
    (codesByParent[c.parent] ||= []).push(c);
  });

  const thoughtHtml = (t.thoughts || []).map(th => {
    const kids = codesByParent[th.id] || [];
    const open = th.kept ? 'open' : '';
    return `
      <div class="thought ${th.kept?'kept':'pruned'} ${open}">
        <div class="thought-head">
          <strong>${esc(th.id)}</strong>
          <span class="tag ${th.kept?'kept':'pruned'}">${th.kept?'KEPT':'PRUNED'}</span>
          <span class="tag">value ${th.value ?? '?'}</span>
          <span class="tag">${th.tokens ?? 0} tok</span>
          <span class="tag">${kids.length} code(s)</span>
        </div>
        <div class="thought-body">
          <div class="prompt">${esc(th.thought || '')}</div>
          <div class="codes">${kids.map(codeBlock).join('') || '<div class="meta">无代码子节点</div>'}</div>
        </div>
      </div>`;
  }).join('');

  detail.innerHTML = `
    <div class="stats">
      <div class="stat"><div class="l">Task</div><div class="v">#${t.task_id}</div></div>
      <div class="stat"><div class="l">Result</div><div class="v" style="color:${t.passed?'var(--green)':'var(--red)'}">${t.passed?'PASS':'FAIL'}</div></div>
      <div class="stat"><div class="l">Tree</div><div class="v">${t.num_thoughts}→${t.num_kept}→${t.num_code}</div></div>
      <div class="stat"><div class="l">Tokens</div><div class="v">${t.tokens ?? 0}</div></div>
      <div class="stat"><div class="l">Selected</div><div class="v" style="font-size:0.85rem">${esc(t.selected_id || '-')}</div></div>
    </div>
    <div class="section">
      <h2>题目 Prompt</h2>
      <div class="prompt">${esc(t.prompt || '')}</div>
    </div>
    <div class="section">
      <h2>搜索树（Thought → Code）</h2>
      <p class="legend">蓝色边框 = 保留到 beam 的计划；绿色高亮 = 最终 selected 代码。点击计划行可展开/收起。</p>
      <div class="tree">${thoughtHtml}</div>
    </div>`;

  detail.querySelectorAll('.thought-head').forEach(head => {
    head.addEventListener('click', () => head.parentElement.classList.toggle('open'));
  });
  history.replaceState(null, '', '#task-' + taskId);
}

document.getElementById('q').addEventListener('input', applyFilter);
document.getElementById('filter').addEventListener('change', applyFilter);
document.getElementById('expandAll').addEventListener('click', () => {
  document.querySelectorAll('.thought').forEach(n => n.classList.add('open'));
});
document.getElementById('collapseAll').addEventListener('click', () => {
  document.querySelectorAll('.thought').forEach(n => n.classList.remove('open'));
});

applyFilter();
const hash = location.hash.match(/task-(\d+)/);
if (hash) selectTask(Number(hash[1]));
else if (filtered.length) selectTask(filtered[0].task_id);
</script>
</body>
</html>
"""


def main() -> None:
    """读取 records → 写 compact JSON + HTML。"""
    args = parse_args()
    if not args.records.exists():
        raise FileNotFoundError(f"Missing records: {args.records}")

    tasks = []
    with args.records.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tasks.append(
                    compact_record(
                        json.loads(line),
                        thought_chars=args.thought_chars,
                        code_chars=args.code_chars,
                        prompt_chars=args.prompt_chars,
                    )
                )

    args.compact_json.parent.mkdir(parents=True, exist_ok=True)
    args.compact_json.write_text(
        json.dumps(tasks, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    args.html.write_text(build_html(tasks), encoding="utf-8")
    print(f"tasks={len(tasks)} passed={sum(1 for t in tasks if t['passed'])}")
    print(f"Wrote {args.compact_json}")
    print(f"Wrote {args.html}")


if __name__ == "__main__":
    main()
