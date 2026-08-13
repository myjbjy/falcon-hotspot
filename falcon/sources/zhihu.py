"""知乎热榜（api.zhihu.com/topstory/hot-list，JSON 老接口，无需签名）。"""
from __future__ import annotations

import re

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Referer": "https://www.zhihu.com/"}


def _parse_heat(text: str) -> int:
    """'4873 万热度' → 48730000；'9876 热度' → 9876。"""
    m = re.search(r"([\d.]+)\s*万", text or "")
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"(\d+)", text or "")
    return int(m.group(1)) if m else 0


class ZhihuSource(BaseSource):
    name = "zhihu"
    label = "知乎热榜"
    weight = 1.3

    def fetch(self) -> list[Item]:
        import json
        import urllib.request
        req = urllib.request.Request("https://api.zhihu.com/topstory/hot-list?limit=50", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        items: list[Item] = []
        for i, row in enumerate(data.get("data", []), 1):
            t = row.get("target") or {}
            title = clean_text(t.get("title", ""))
            if not title:
                continue
            tid = t.get("id", "")
            ttype = t.get("type", "")
            if ttype == "question":
                url = f"https://www.zhihu.com/question/{tid}"
            elif ttype == "article":
                url = f"https://zhuanlan.zhihu.com/p/{tid}"
            else:
                url = t.get("url", "")
            items.append(Item(
                source=self.name, title=title, url=url,
                rank=i, heat=_parse_heat(row.get("detail_text", "")),
                desc=clean_text(t.get("excerpt", ""))[:120],
                tags=[ttype],
            ))
        return items[: self.limit]
