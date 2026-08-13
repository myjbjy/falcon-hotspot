"""IT之家热榜（ithome.com/block/rank.html，HTML 解析）。"""
from __future__ import annotations

import re

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}


class ITHomeSource(BaseSource):
    name = "ithome"
    label = "IT之家"
    weight = 1.1

    def fetch(self) -> list[Item]:
        import urllib.request
        req = urllib.request.Request("https://www.ithome.com/block/rank.html", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            page = r.read().decode("utf-8", "ignore")
        items: list[Item] = []
        # 榜单结构：<a title="标题" target="_blank" href="https://www.ithome.com/0/xxx/yyy.htm">标题</a>
        seen = set()
        for i, m in enumerate(re.finditer(r'<a[^>]+title="([^"]+)"[^>]+href="(https://www\.ithome\.com/[^"]+\.htm)"', page), 1):
            title = clean_text(m.group(1))
            url = m.group(2)
            if not title or len(title) < 4 or url in seen:
                continue
            seen.add(url)
            items.append(Item(source=self.name, title=title, url=url, rank=i))
        return items[: self.limit]
