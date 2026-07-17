#!/usr/bin/env python3
"""
功能: 根据实验结果生成 results.html 展示页。

输入: 实验结果/manifest 等汇总数据
输出: reports/results.html
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / "reports" / "experiment_report.json"
OUT_HTML = ROOT / "reports" / "results.html"


def fmt_params(n: int) -> str:
    """格式化可训练参数量显示。"""
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}K"
    return str(n)


def fmt_mem(mib: int) -> str:
    """格式化显存 MiB 显示。"""
    return f"{mib / 1024:.1f} GB"


def hbars(items: list[tuple[str, float]], maxv: float, color: str, suffix: str = "") -> str:
    """生成横向条形图 HTML 片段。"""
    out = ['<div class="hbar-list">']
    for name, val in items:
        pct = max(2.0, min(100.0, val / maxv * 100))
        out.append(
            '<div class="hbar-row">'
            f'<div class="hbar-label">{escape(name)}</div>'
            f'<div class="hbar-track"><div class="hbar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'<div class="hbar-val">{val}{suffix}</div>'
            "</div>"
        )
    out.append("</div>")
    return "\n".join(out)


def table_rows(data: list[dict], highlight_id: str | None = None) -> str:
    """生成结果表格行 HTML。"""
    trs = []
    for r in data:
        cls = ' class="best"' if r["id"] == highlight_id else ""
        trs.append(
            f"<tr{cls}>"
            f'<td><code>{escape(r["id"])}</code></td>'
            f'<td>{escape(r["type"])}</td>'
            f'<td>{r["rank"]}/{r["alpha"]}</td>'
            f'<td>{escape(str(r["target"]))}</td>'
            f'<td>{r["quant"]}</td>'
            f'<td>{r["epoch"]}</td>'
            f'<td><strong>{r["pass1"]:.2f}%</strong></td>'
            f'<td>{r["peak_mib"]}</td>'
            f'<td>{r["steps"]:.2f}</td>'
            f'<td>{fmt_params(r["trainable"])} ({r["trainable_pct"]}%)</td>'
            f'<td>{r["loss"]:.3f}</td>'
            "</tr>"
        )
    return "\n".join(trs)


def main() -> None:
    """组装并写出 results.html。"""
    d = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    baseline = d["baseline"]
    bp = round(baseline["mbpp_metrics"]["pass_at_1"] * 100, 2)
    bs = round(baseline["mbpp_metrics"]["syntax_pass_rate"] * 100, 2)
    bst = baseline["train_results"]["train_steps_per_second"]
    brt = baseline["train_results"]["train_runtime"]

    rows = []
    for r in d["runs"]:
        p, res, m = r["params"], r["resources"], r["metrics"]
        rows.append(
            {
                "id": r["run_id"],
                "phase": r["phase"],
                "type": p.get("finetuning_type"),
                "rank": p["lora_rank"],
                "alpha": p["lora_alpha"],
                "target": p.get("lora_target_key") or p.get("lora_target"),
                "quant": "4bit" if p.get("quantization_bit") == 4 else "none",
                "epoch": p["num_train_epochs"],
                "pass1": round(m["pass_at_1"] * 100, 2),
                "peak_mib": res["gpu_memory_peak_mib"],
                "steps": res["train_steps_per_second"],
                "trainable": res["trainable_params"],
                "trainable_pct": res["trainable_pct"],
                "loss": round(res["train_loss"], 3),
                "runtime": round(res["train_runtime_sec"], 1),
            }
        )

    phase1 = [r for r in rows if r["phase"] == "grid"]
    phase2 = sorted([r for r in rows if r["phase"] == "alpha_sweep"], key=lambda x: x["alpha"])
    phase3 = [r for r in rows if r["phase"] == "epoch_sweep"]
    phase1_sorted = sorted(phase1, key=lambda x: -x["pass1"])
    overall = max(rows, key=lambda x: x["pass1"])
    p1best = phase1_sorted[0]
    fastest = max(phase1, key=lambda x: x["steps"])
    lowest_mem = min(phase1, key=lambda x: x["peak_mib"])
    ep1 = next(r for r in phase3 if r["epoch"] == 1)
    ep5 = next(r for r in phase3 if r["epoch"] == 5)

    pass_items = [("Full SFT", bp)] + [(r["id"], r["pass1"]) for r in phase1_sorted]
    pass_max = max(v for _, v in pass_items) * 1.15
    bl_peak = baseline.get("gpu_memory_peak_mib")
    mem_items = [(r["id"], r["peak_mib"]) for r in phase1]
    if bl_peak is not None:
        mem_items = [("Full SFT", int(bl_peak))] + mem_items
    mem_max = max(v for _, v in mem_items)
    speed_items = [("Full SFT", bst)] + [(r["id"], r["steps"]) for r in phase1]
    speed_max = max(v for _, v in speed_items) * 1.1
    delta = p1best["pass1"] - bp

    alpha_trs = []
    for r in phase2:
        cls = ' class="best"' if r["id"] == overall["id"] else ""
        alpha_trs.append(
            f"<tr{cls}><td>{r['alpha']}</td><td>{r['alpha'] / r['rank']:g}×rank</td>"
            f"<td><strong>{r['pass1']:.2f}%</strong></td><td>{r['loss']:.3f}</td></tr>"
        )

    parts: list[str] = []
    parts.append(
        """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LoRA / QLoRA SFT 实验结果</title>
<style>
  :root {
    --bg: #f7f7f5;
    --panel: #ffffff;
    --text: #1c1917;
    --muted: #78716c;
    --line: #e7e5e4;
    --accent: #1d4ed8;
    --good: #15803d;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", "PingFang SC", "Noto Sans CJK SC", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 28px 20px 48px; }
  h1 { font-size: 28px; margin: 0 0 6px; letter-spacing: -0.02em; }
  h2 { font-size: 18px; margin: 28px 0 10px; }
  h3 { font-size: 15px; margin: 0 0 8px; }
  .sub { color: var(--muted); margin: 0 0 20px; font-size: 14px; }
  .badge {
    display: inline-block; font-size: 12px; padding: 2px 8px; border-radius: 999px;
    background: #dcfce7; color: var(--good); font-weight: 600; margin-left: 8px;
    vertical-align: middle;
  }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
  .stat {
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px;
  }
  .stat .v { font-size: 26px; font-weight: 700; letter-spacing: -0.03em; }
  .stat .l { font-size: 12px; color: var(--muted); margin-top: 4px; }
  .stat.good .v { color: var(--good); }
  .stat.info .v { color: var(--accent); }
  .callout {
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 14px 16px;
    font-size: 14px; margin-bottom: 8px;
  }
  .callout strong { color: var(--good); }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .panel {
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px;
  }
  table {
    width: 100%; border-collapse: collapse; font-size: 13px; background: var(--panel);
    border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
  }
  th, td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; }
  th { background: #fafaf9; color: var(--muted); font-weight: 600; font-size: 12px; }
  tr.best { background: #f0fdf4; }
  tr:last-child td { border-bottom: 0; }
  code { font-size: 12px; }
  .hbar-list { display: flex; flex-direction: column; gap: 8px; }
  .hbar-row { display: grid; grid-template-columns: minmax(120px, 180px) 1fr 70px; gap: 8px; align-items: center; font-size: 12px; }
  .hbar-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); }
  .hbar-track { height: 10px; background: #f5f5f4; border-radius: 999px; overflow: hidden; }
  .hbar-fill { height: 100%; border-radius: 999px; }
  .hbar-val { text-align: right; font-variant-numeric: tabular-nums; }
  .note { color: var(--muted); font-size: 12px; margin-top: 8px; }
  .foot { color: #a8a29e; font-size: 12px; margin-top: 28px; }
  @media (max-width: 900px) { .stats, .grid2 { grid-template-columns: 1fr 1fr; } }
  @media (max-width: 640px) {
    .stats, .grid2 { grid-template-columns: 1fr; }
    .hbar-row { grid-template-columns: 1fr; gap: 4px; }
  }
</style>
</head>
<body>
<div class="wrap">
"""
    )

    parts.append(
        f'<h1>LoRA / QLoRA SFT 实验结果 <span class="badge">13/13 完成</span></h1>'
        '<p class="sub">Qwen1.5-0.5B-Chat · MBPP sanitized (257 题) · '
        "lora_dropout=0.05 · lr=1e-4 · 数据源：sft/lora2_exp_cgh/reports</p>"
    )
    parts.append("<div class=\"stats\">")
    parts.append(
        f'<div class="stat good"><div class="v">{overall["pass1"]:.2f}%</div>'
        f'<div class="l">全局最优 pass@1 · {escape(overall["id"])}</div></div>'
    )
    parts.append(
        f'<div class="stat info"><div class="v">{p1best["pass1"]:.2f}%</div>'
        f'<div class="l">Phase1 最优 · {escape(p1best["id"])}</div></div>'
    )
    parts.append(
        f'<div class="stat"><div class="v">{fmt_mem(lowest_mem["peak_mib"])}</div>'
        f'<div class="l">Phase1 最低峰值显存 · {escape(lowest_mem["id"])}</div></div>'
    )
    parts.append(
        f'<div class="stat"><div class="v">{fastest["steps"]:.2f}</div>'
        f'<div class="l">Phase1 最快步/秒 · {escape(fastest["id"])}</div></div>'
    )
    parts.append("</div>")

    parts.append(
        '<div class="callout"><strong>核心结论：</strong>'
        "Phase1 最优为 QLoRA <code>r8_tqv_q4</code>（rank=8, α=16, q/v, 4bit）："
        f'pass@1 {p1best["pass1"]}%（相对 Full SFT {bp}% +{delta:.2f}pp），'
        f'仅训练 {fmt_params(p1best["trainable"])} 参数（{p1best["trainable_pct"]}%）。'
        f'Phase2 将 α 降至 1×rank 后进一步提升到 {overall["pass1"]}%；'
        "α=4×rank 与 epoch=5 均出现过拟合回落。</div>"
    )

    parts.append('<h2>Phase1 主网格 · pass@1（%）</h2><div class="panel">')
    parts.append(hbars(pass_items, pass_max, "#2563eb", "%"))
    parts.append(f'<p class="note">参考：Full SFT baseline = {bp}%</p></div>')

    parts.append('<div class="grid2" style="margin-top:16px">')
    parts.append('<div class="panel"><h3>峰值显存 (MiB)</h3>')
    parts.append(hbars(mem_items, mem_max, "#d97706"))
    parts.append(
        f'<p class="note">r16_tall LoRA {fmt_mem(19133)} → QLoRA {fmt_mem(11495)}（约 −40%）</p></div>'
    )
    parts.append('<div class="panel"><h3>训练速度 (步/秒)</h3>')
    parts.append(hbars(speed_items, speed_max, "#15803d"))
    parts.append(f'<p class="note">Full SFT = {bst} 步/秒</p></div></div>')

    parts.append(
        '<h2>Phase1 完整对比</h2><div style="overflow-x:auto"><table><thead><tr>'
        "<th>实验</th><th>类型</th><th>r/α</th><th>target</th><th>quant</th><th>epoch</th>"
        "<th>pass@1</th><th>峰值显存</th><th>步/秒</th><th>可训练参数</th><th>训练损失</th>"
        "</tr></thead><tbody>"
    )
    bl_loss = round(float(baseline["train_results"].get("train_loss", 0)), 3)
    bl_peak = baseline.get("gpu_memory_peak_mib")
    bl_peak_s = str(bl_peak) if bl_peak is not None else "—"
    parts.append(
        "<tr>"
        "<td><code>Full SFT</code></td>"
        "<td>full</td><td>—</td><td>—</td><td>—</td>"
        f"<td>{baseline['train_results'].get('epoch', 3.0)}</td>"
        f"<td><strong>{bp:.2f}%</strong></td>"
        f"<td>{bl_peak_s}</td>"
        f"<td>{bst:.2f}</td>"
        "<td>全部 (100%)</td>"
        f"<td>{bl_loss:.3f}</td>"
        "</tr>"
    )
    parts.append(table_rows(phase1_sorted, p1best["id"]))
    parts.append("</tbody></table></div>")
    parts.append(
        f'<p class="note">Baseline Full SFT：pass@1 {bp}% · 语法 {bs}% · '
        f"{bst} 步/秒 · 可训练 100% · 耗时 {brt:.0f}s · 峰显存 {bl_peak_s} MiB"
        f"（30-step probe，同 batch/seq/fp16）</p>"
    )

    parts.append('<div class="grid2" style="margin-top:8px"><div>')
    parts.append('<h2>Phase2 · Alpha Sweep</h2><div class="panel" style="margin-bottom:10px">')
    parts.append(hbars([(f'α={r["alpha"]}', r["pass1"]) for r in phase2], 4.5, "#2563eb", "%"))
    parts.append(
        '</div><table><thead><tr><th>α</th><th>倍率</th><th>pass@1</th><th>训练损失</th>'
        "</tr></thead><tbody>"
    )
    parts.append("\n".join(alpha_trs))
    parts.append('</tbody></table></div><div>')
    parts.append('<h2>Phase3 · Epoch Sweep</h2><div class="panel" style="margin-bottom:10px">')
    parts.append(
        hbars(
            [
                ("ep=1", ep1["pass1"]),
                ("ep=3 (Phase1)", p1best["pass1"]),
                ("ep=5", ep5["pass1"]),
            ],
            4.5,
            "#2563eb",
            "%",
        )
    )
    parts.append(
        '</div><table><thead><tr><th>epoch</th><th>pass@1</th><th>耗时(s)</th><th>训练损失</th>'
        "</tr></thead><tbody>"
    )
    parts.append(
        f'<tr><td>1</td><td><strong>{ep1["pass1"]:.2f}%</strong></td>'
        f'<td>{ep1["runtime"]}</td><td>{ep1["loss"]:.3f}</td></tr>'
    )
    parts.append(
        f'<tr class="best"><td>3</td><td><strong>{p1best["pass1"]:.2f}%</strong></td>'
        f'<td>{p1best["runtime"]}</td><td>{p1best["loss"]:.3f}</td></tr>'
    )
    parts.append(
        f'<tr><td>5</td><td><strong>{ep5["pass1"]:.2f}%</strong></td>'
        f'<td>{ep5["runtime"]}</td><td>{ep5["loss"]:.3f}</td></tr>'
    )
    parts.append("</tbody></table></div></div>")

    parts.append(
        "<h2>推荐配置</h2><table><thead><tr>"
        "<th>用途</th><th>配置</th><th>pass@1</th><th>显存</th><th>速度</th><th>理由</th>"
        "</tr></thead><tbody>"
    )
    parts.append(
        f'<tr class="best"><td>精度优先</td><td>QLoRA r8 q/v α=8 epoch=3</td>'
        f'<td>{overall["pass1"]}%</td><td>{fmt_mem(overall["peak_mib"])}</td>'
        f'<td>{overall["steps"]}</td><td>全局最高 pass@1</td></tr>'
    )
    parts.append(
        f'<tr><td>Phase1 默认</td><td>QLoRA r8 q/v α=16 epoch=3</td>'
        f'<td>{p1best["pass1"]}%</td><td>{fmt_mem(p1best["peak_mib"])}</td>'
        f'<td>{p1best["steps"]}</td><td>网格最优，参数量最低档</td></tr>'
    )
    parts.append(
        "<tr><td>速度优先</td><td>LoRA r8 q/v α=16 epoch=3</td>"
        "<td>3.11%</td><td>11.8 GB</td><td>1.09</td><td>持平 baseline，吞吐最高</td></tr>"
    )
    parts.append("</tbody></table>")

    parts.append(
        '<p class="foot">Source: sft/lora2_exp_cgh/reports/experiment_report.json · '
        "generated 2026-07-05 · GPU total 23552 MiB<br>"
        "本页为 Canvas 的浏览器可读替代版，位于工作区内可直接打开。</p>"
        "</div></body></html>"
    )

    OUT_HTML.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
