"""贴吧热议（tieba.baidu.com/hottopic，JSON API）。"""
from __future__ import annotations

import json

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9",
      "Referer": "https://tieba.baidu.com/"}


class TiebaSource(BaseSource):
    name = "tieba"
    label = "贴吧热议"
    weight = 1.1

    def fetch(self) -> list[Item]:
        import urllib.request
        req = urllib.request.Request("https://tieba.baidu.com/hottopic/browse/topicList", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        items: list[Item] = []
        d = data.get("data") or {}
        # bang_topic 是 dict {module_title, topic_list}；sug_topic/manual_topic 同构
        topic_list = []
        for key in ("bang_topic", "sug_topic", "manual_topic"):
            section = d.get(key) or {}
            topic_list.extend(section.get("topic_list") or [])
        seen = set()
        for i, row in enumerate(topic_list, 1):
            title = clean_text(row.get("topic_name", ""))
            if not title or title in seen:
                continue
            seen.add(title)
            items.append(Item(
                source=self.name, title=title,
                url=row.get("topic_url", "") or f"https://tieba.baidu.com/f?kw={title}",
                rank=i, heat=int(row.get("total_num", 0) or 0),
                desc=clean_text(row.get("topic_desc", "")),
            ))
        return items[: self.limit]
