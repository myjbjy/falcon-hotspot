"""V2EX 热帖（v2ex.com/api/topics/hot.json，JSON API）。"""
from __future__ import annotations

import json

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json",
      "Accept-Language": "zh-CN,zh;q=0.9"}


class V2EXSource(BaseSource):
    name = "v2ex"
    label = "V2EX"
    weight = 1.1

    def fetch(self) -> list[Item]:
        import urllib.request
        req = urllib.request.Request("https://www.v2ex.com/api/topics/hot.json", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            rows = json.loads(r.read().decode("utf-8", "ignore"))
        items: list[Item] = []
        for i, row in enumerate(rows, 1):
            title = clean_text(row.get("title", ""))
            if not title:
                continue
            items.append(Item(
                source=self.name, title=title,
                url=row.get("url", ""),
                rank=i, heat=int(row.get("replies", 0) or 0),
                desc=clean_text(row.get("content_rendered", ""))[:120],
                tags=[row.get("node", {}).get("title", "")] if row.get("node") else [],
            ))
        return items[: self.limit]
