"""微博实时热搜（s.weibo.com/top/summary，HTML 解析）。"""
from __future__ import annotations

import re

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}


class WeiboSource(BaseSource):
    name = "weibo"
    label = "微博热搜"
    weight = 1.4

    def fetch(self) -> list[Item]:
        import urllib.request
        req = urllib.request.Request("https://s.weibo.com/top/summary?cate=realtimehot", headers=UA)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            page = r.read().decode("utf-8", "ignore")
        items: list[Item] = []
        # 每个 <tr> 一块；实时热搜在 tbody 内
        for tr in re.split(r"<tr", page)[1:]:
            try:
                # 排名
                rm = re.search(r'class="num">\s*(\d+)', tr)
                # 标题与链接
                tm = re.search(r'href="(/weibo\?q=[^"]+)"[^>]*>(.*?)</a>', tr, re.S)
                # 热度（如 1234567 或 "新"）
                hm = re.search(r'class="td-02">.*?</span>\s*([\d,]+)', tr, re.S)
                if not tm:
                    continue
                title = clean_text(tm.group(2))
                if not title or title == "置顶":
                    continue
                rank = int(rm.group(1)) if rm else 0
                heat_txt = hm.group(1).replace(",", "") if hm else ""
                items.append(Item(
                    source=self.name, title=title,
                    url="https://s.weibo.com" + tm.group(1),
                    rank=rank, heat=int(heat_txt) if heat_txt.isdigit() else 0,
                ))
            except Exception:
                continue
        return items[: self.limit]
