"""百度实时热搜（top.baidu.com/board，解析嵌入的 __INITIAL_STATE__ JSON，带 TLS 重试）。

注意：百度对该接口有偶发 TLS 层重置（UNEXPECTED_EOF_WHILE_READING），
通过新建连接重试（最多 retries 次）可显著提高成功率。
"""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "zh-CN,zh;q=0.9"}


def _fetch(url: str, retries: int = 3) -> str:
    last = None
    for i in range(retries):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
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
        items: list[Item] = []
        m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>", page, re.S)
        if m:
            try:
                state = json.loads(m.group(1))
                cards = state.get("data", {}).get("cardlistInfo", {}).get("cards", [])
                for card in cards:
                    for c in card.get("content", []):
                        title = clean_text(c.get("word", ""))
                        title = re.sub(r"\s*(热|新|沸|爆|荐)$", "", title)  # 去榜单状态后缀
                        if not title:
                            continue
                        url = c.get("url", "") or f"https://www.baidu.com/s?wd={title}"
                        desc = clean_text(c.get("desc", ""))
                        heat = int(c.get("hotScore", 0) or 0)
                        items.append(Item(source=self.name, title=title, url=url,
                                          rank=len(items) + 1, heat=heat, desc=desc))
            except Exception:
                items = []
        if not items:
            for i, block in enumerate(re.split(r'class="category-wrap', page)[1:], 1):
                tm = re.search(r'class="title[^"]*"[^>]*>(.*?)</a>', block, re.S)
                hm = re.search(r'class="hot-index[^"]*">([\d,]+)', block)
                if not tm:
                    continue
                title = clean_text(tm.group(1))
                if not title:
                    continue
                heat = hm.group(1).replace(",", "") if hm else ""
                items.append(Item(source=self.name, title=title,
                                  url=f"https://www.baidu.com/s?wd={title}",
                                  rank=i, heat=int(heat) if heat.isdigit() else 0))
        return items[: self.limit]
