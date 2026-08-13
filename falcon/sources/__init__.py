"""数据源注册表。新增源：写一个 source 类 → 在此 import 并加入 REGISTRY。"""
from __future__ import annotations

from .base import BaseSource, Item, clean_text
from .weibo import WeiboSource
from .zhihu import ZhihuSource
from .tieba import TiebaSource
from .baidu import BaiduSource
from .toutiao import ToutiaoSource
from .ithome import ITHomeSource
from .v2ex import V2EXSource
from .hackernews import HackerNewsSource
from .github_trending import GitHubTrendingSource
from .csdn import CSDNSource

REGISTRY: dict[str, type[BaseSource]] = {
    cls.name: cls for cls in (
        WeiboSource,
        ZhihuSource,
        TiebaSource,
        BaiduSource,
        ToutiaoSource,
        ITHomeSource,
        V2EXSource,
        HackerNewsSource,
        GitHubTrendingSource,
        CSDNSource,
    )
}


def get_source(name: str) -> BaseSource:
    return REGISTRY[name]()


def all_sources(only: Optional[list[str]] = None) -> list[BaseSource]:
    """实例化全部（或指定）数据源。"""
    names = only or list(REGISTRY.keys())
    return [REGISTRY[n]() for n in names if n in REGISTRY]


def source_labels() -> dict[str, str]:
    return {n: cls.label for n, cls in REGISTRY.items()}


from typing import Optional  # noqa: E402
