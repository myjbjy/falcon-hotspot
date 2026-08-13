"""微博实时热搜（weibo.com/ajax/side/hotSearch，JSON）。

注意：必须带 Referer: https://weibo.com/ 否则 403。
"""
from __future__ import annotations

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Referer": "https://weibo.com/"}


class WeiboSource(BaseSource):
    name = "weibo"
    label = "微博热搜"
    weight = 1.4

    def fetch(self) -> list[Item]:
        import json
        import urllib.request
        req = urllib.request.Request("https://weibo.com/ajax/side/hotSearch", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        items: list[Item] = []
        realtime = (data.get("data") or {}).get("realtime") or []
        for i, row in enumerate(realtime, 1):
            word = clean_text(row.get("word", ""))
            if not word:
                continue
            # word_scheme 如 #朱镕基同志逝世# → 搜索链接
            scheme = row.get("word_scheme") or ""
            if scheme.startswith("#"):
                url = "https://s.weibo.com/weibo?q=" + urllib.parse.quote(scheme)
            else:
                url = "https://s.weibo.com/weibo?q=" + urllib.parse.quote(word)
            items.append(Item(
                source=self.name, title=word, url=url,
                rank=i, heat=int(row.get("num", 0) or 0),
                desc=clean_text(row.get("label_name", "")),
            ))
        return items[: self.limit]
