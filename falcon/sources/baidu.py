"""百度实时热搜（top.baidu.com/board，HTML 解析）。

注意：
- 百度对 urllib 有偶发 TLS 层重置（UNEXPECTED_EOF_WHILE_READING），重试可解决
- 页面结构动态变化（__INITIAL_STATE__ 时有时无），实测 HTML 正则最稳定：
  标题在 class="title_*" 内（嵌套 div.c-single-text-ellipsis），热度在 class="hot-index_*" 内
"""
from __future__ import annotations

import re
import ssl
import time
import urllib.request

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}

TITLE_RE = re.compile(r'class="title[^"]*"[^>]*>(.*?)</a>', re.S)
HEAT_RE = re.compile(r'class="hot-index[^"]*">\s*([\d,]+)\s*<')


def _fetch(url: str, retries: int = 4) -> str:
    last = None
    for i in range(retries):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


class BaiduSource(BaseSource):
    name = "baidu"
    label = "百度热搜"
    weight = 1.2

    def fetch(self) -> list[Item]:
        page = _fetch("https://top.baidu.com/board?tab=realtime")
        blocks = re.split(r'class="category-wrap', page)[1:]
        items: list[Item] = []
        for block in blocks:
            tm = TITLE_RE.search(block)
            hm = HEAT_RE.search(block)
            if not tm:
                continue
            title = clean_text(tm.group(1))
            # 去榜单状态后缀
            title = re.sub(r"\s*(热|新|沸|爆|荐)$", "", title)
            if not title:
                continue
            heat = hm.group(1).replace(",", "") if hm else ""
            items.append(Item(
                source=self.name, title=title,
                url=f"https://www.baidu.com/s?wd={title}",
                rank=len(items) + 1, heat=int(heat) if heat.isdigit() else 0,
            ))
        return items[: self.limit]
