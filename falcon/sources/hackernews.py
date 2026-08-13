"""Hacker News Top（firebaseio API，JSON，并行抓取详情加速）。"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json"}


class HackerNewsSource(BaseSource):
    name = "hackernews"
    label = "Hacker News"
    weight = 1.0

    def fetch(self) -> list[Item]:
        import urllib.request
        req = urllib.request.Request("https://hacker-news.firebaseio.com/v0/topstories.json", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            ids = json.loads(r.read().decode("utf-8", "ignore"))[:30]

        def load_one(sid: int) -> dict | None:
            try:
                req2 = urllib.request.Request(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", headers=UA)
                with urllib.request.urlopen(req2, timeout=self.timeout) as r2:
                    return json.loads(r2.read().decode("utf-8", "ignore"))
            except Exception:
                return None

        items: list[Item] = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            rows = ex.map(load_one, ids)
        for rank, row in enumerate(rows, 1):
            if not row:
                continue
            title = clean_text(row.get("title", ""))
            if not title:
                continue
            sid = row.get("id")
            url = row.get("url") or f"https://news.ycombinator.com/item?id={sid}"
            items.append(Item(source=self.name, title=title, url=url,
                              rank=rank, heat=int(row.get("score", 0) or 0),
                              desc=f"{row.get('descendants', 0)} comments"))
        return items[: self.limit]
