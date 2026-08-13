"""头条热榜（toutiao.com/hot-event/hot-board，JSON API）。"""
from __future__ import annotations

import json

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Referer": "https://www.toutiao.com/"}


class ToutiaoSource(BaseSource):
    name = "toutiao"
    label = "头条热榜"
    weight = 1.2

    def fetch(self) -> list[Item]:
        import urllib.request
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        items: list[Item] = []
        for i, row in enumerate(data.get("data", []), 1):
            title = clean_text(row.get("Title", ""))
            if not title:
                continue
            items.append(Item(
                source=self.name, title=title,
                url=row.get("Url", "") or row.get("ClusterUrl", ""),
                rank=i, heat=int(row.get("HotValue", 0) or 0),
                desc=clean_text(row.get("Label", "")),
            ))
        return items[: self.limit]
