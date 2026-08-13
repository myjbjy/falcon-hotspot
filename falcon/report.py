"""报告层：生成每日热点日报（Markdown + 自包含 HTML）与站点数据。

产物：
- site/daily/YYYY-MM-DD.md    人读日报（含跨源热点 + 各源榜单）
- site/daily/YYYY-MM-DD.html  自包含 HTML 版
- site/history.json           每日汇总历史（站点趋势图数据源）
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from . import storage

CSS = """
<style>
body{font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;max-width:860px;margin:0 auto;padding:24px;color:#222;line-height:1.7}
h1{font-size:1.6em;border-bottom:2px solid #ff6a00;padding-bottom:8px}
h2{font-size:1.2em;margin-top:28px;color:#ff6a00}
a{color:#0366d6;text-decoration:none}a:hover{text-decoration:underline}
.topic{background:#fff8f0;border-left:4px solid #ff6a00;padding:8px 14px;margin:8px 0;border-radius:4px}
.topic .src{color:#888;font-size:.85em}
ol li{margin:4px 0}
.fail{color:#c0392b;font-weight:bold}
.meta{color:#888;font-size:.85em}
</style>
"""


def _fmt_heat(h: int) -> str:
    if h >= 10000:
        return f"{h / 10000:.1f}万"
    return str(h)


def render_md(analysis: dict, date_str: str, llm_brief: str = "") -> str:
    stats = analysis["stats"]
    labels = stats.get("source_labels", {})
    lines = [f"# 🦅 猎鹰热点日报 {date_str}", ""]
    lines.append(f"> 跨源聚合 · {stats['total_items']} 条采集 · {stats['total_topics']} 个主题 · "
                 f"成功源 {stats['ok_sources']}/{stats['total_sources']}")
    lines.append("")
    if llm_brief:
        lines.append("## 📝 今日解读")
        lines.append(llm_brief.strip())
        lines.append("")

    lines.append("## 🔥 全网跨源热点 TOP10")
    lines.append("")
    for t in analysis["topics"][:10]:
        srcs = "、".join(labels.get(s, s) for s in t["sources"])
        heat = f" · 热度 {_fmt_heat(t['heat_sum'])}" if t["heat_sum"] else ""
        lines.append(f"{t['rank']}. **{t['title']}**（{t['source_count']}源: {srcs}）{heat}")
    lines.append("")

    for name, items in analysis["per_source"].items():
        lab = labels.get(name, name)
        lines.append(f"## 📡 {lab} TOP10")
        lines.append("")
        for it in items[:10]:
            heat = f"（热度 {_fmt_heat(it['heat'])}）" if it.get("heat") else ""
            lines.append(f"{it['rank']}. [{it['title']}]({it['url']}){heat}")
        lines.append("")

    # 失败源提示
    fails = [n for n, s in analysis.get("source_status", {}).items() if not s.get("ok")]
    if fails:
        lines.append(f"## ⚠️ 采集异常")
        for n in fails:
            lines.append(f"- {labels.get(n, n)}: {analysis['source_status'][n].get('error', 'unknown')}")
        lines.append("")
    lines.append("---")
    lines.append(f"*由 Falcon Hotspot 自动生成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    return "\n".join(lines)


def render_html(md_text: str, date_str: str) -> str:
    import markdown
    try:
        body = markdown.markdown(md_text, extensions=["extra"])
    except Exception:
        import re
        body = "<pre>" + md_text + "</pre>"
    return f"<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'>" \
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>" \
           f"<title>猎鹰热点日报 {date_str}</title>{CSS}</head><body>{body}</body></html>"


def update_history(analysis: dict, date_str: str) -> None:
    """追加当日汇总到 history.json（站点趋势图数据）。"""
    history = []
    hp = os.path.join(storage.SITE_DIR, "history.json")
    if os.path.exists(hp):
        try:
            with open(hp, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    entry = {
        "date": date_str,
        "total_items": analysis["stats"]["total_items"],
        "total_topics": analysis["stats"]["total_topics"],
        "cross_source_topics": analysis["stats"]["cross_source_topics"],
        "ok_sources": analysis["stats"]["ok_sources"],
    }
    history = [e for e in history if e.get("date") != date_str] + [entry]
    history.sort(key=lambda e: e["date"])
    with open(hp, "w", encoding="utf-8") as f:
        json.dump(history[-90:], f, ensure_ascii=False, indent=1)


def generate(analysis: dict, date_str: str, llm_brief: str = "") -> dict:
    """生成全部报告产物，返回路径字典。"""
    md_text = render_md(analysis, date_str, llm_brief)
    md_path = storage.save_site_file(f"daily/{date_str}.md", md_text)
    html_path = storage.save_site_file(f"daily/{date_str}.html", render_html(md_text, date_str))
    update_history(analysis, date_str)
    return {"md": md_path, "html": html_path}
