"""CSDN 热榜（blog.csdn.net/phoenix/web/blog/hot-rank，JSON）。"""
from __future__ import annotations

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Referer": "https://blog.csdn.net/"}


class CSDNSource(BaseSource):
    name = "csdn"
    label = "CSDN 热榜"
    weight = 1.0

    def fetch(self) -> list[Item]:
        import json
        import time
        import urllib.request
        # CSDN 偶发慢响应，重试 3 次
        last = None
        for _ in range(3):
            try:
                req = urllib.request.Request(
                    "https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=30", headers=UA)
                with urllib.request.urlopen(req, timeout=25) as r:
                    data = json.loads(r.read().decode("utf-8", "ignore"))
                break
            except Exception as e:
                last = e
                time.sleep(2)
        else:
            raise last
        items: list[Item] = []
        for i, row in enumerate(data.get("data", []), 1):
            title = clean_text(row.get("articleTitle", ""))
            if not title:
                continue
            url = row.get("articleDetailUrl") or ""
            views = int(row.get("viewCount") or 0)
            items.append(Item(
                source=self.name, title=title, url=url,
                rank=i, heat=views,
                desc=f"{row.get('commentCount', 0)}评论 · {row.get('favorCount', 0)}收藏",
            ))
        return items[: self.limit]
