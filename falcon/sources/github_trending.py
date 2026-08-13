"""GitHub Trending（github.com/trending?since=daily，HTML 解析，复用已验证的抓取逻辑）。"""
from __future__ import annotations

import re

from .base import BaseSource, Item, clean_text

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


class GitHubTrendingSource(BaseSource):
    name = "github"
    label = "GitHub Trending"
    weight = 1.1

    def fetch(self) -> list[Item]:
        import urllib.request
        # github.com 直连慢且偶发截断，重试 3 次
        page = ""
        last = None
        for _ in range(3):
            try:
                req = urllib.request.Request("https://github.com/trending?since=daily", headers=UA)
                with urllib.request.urlopen(req, timeout=30) as r:
                    page = r.read().decode("utf-8", "ignore")
                break
            except Exception as e:
                last = e
                import time
                time.sleep(2)
        if not page:
            raise last
        items: list[Item] = []
        for i, art in enumerate(re.split(r"<article", page)[1:], 1):
            try:
                m = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', art, re.S)
                if not m:
                    continue
                full = m.group(1).strip().strip("/")
                dm = re.search(r"</h2>\s*<p[^>]*>(.*?)</p>", art, re.S)
                desc = clean_text(dm.group(1)) if dm else ""
                sm = re.search(r"([\d,]+)\s+stars today", art)
                stars = sm.group(1).replace(",", "") if sm else ""
                items.append(Item(
                    source=self.name, title=full,
                    url=f"https://github.com/{full}",
                    rank=i, heat=int(stars) if stars.isdigit() else 0,
                    desc=desc,
                ))
            except Exception:
                continue
        return items[: self.limit]
