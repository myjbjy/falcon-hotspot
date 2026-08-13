#!/usr/bin/env python3
"""将今日解读插入日报 md（在「全网跨源热点」段之前）。用法: python insert_brief.py <brief_file> <date>"""
import re
import sys
from pathlib import Path

brief = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
date_str = sys.argv[2]
md_path = Path(r"C:\Users\hdec\falcon-hotspot\docs\daily") / f"{date_str}.md"
text = md_path.read_text(encoding="utf-8")

# 删除旧解读段（若有）
text = re.sub(r"## 📝 今日解读\n.*?(?=## )", "", text, flags=re.S)
section = f"## 📝 今日解读\n\n{brief}\n\n"
marker = "## 🔥 全网跨源热点 TOP10"
if marker in text:
    text = text.replace(marker, section + marker, 1)
else:
    text = text + "\n" + section
md_path.write_text(text, encoding="utf-8")
print(f"inserted brief into {md_path}")

# html 版本：简单同步（在 <h2>🔥 全网跨源热点</h2> 前插 <h2>📝 今日解读</h2><p>..</p>）
html_path = md_path.with_suffix(".html")
if html_path.exists():
    h = html_path.read_text(encoding="utf-8")
    h = re.sub(r"<h2>📝 今日解读</h2>.*?(?=<h2>)", "", h, flags=re.S)
    brief_html = brief.replace("\n", "</p>\n<p>")
    section_h = f'<h2>📝 今日解读</h2>\n<p>{brief_html}</p>\n'
    marker_h = "<h2>🔥 全网跨源热点"
    if marker_h in h:
        h = h.replace(marker_h, section_h + marker_h, 1)
    html_path.write_text(h, encoding="utf-8")
    print(f"inserted brief into {html_path}")
