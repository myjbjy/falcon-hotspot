"""统一数据模型与采集器基类。

设计要点（Shell Engineering：代码做骨架）：
- Item 是跨源统一的条目结构，任何 Source 都产出 Item
- BaseSource 定义接口：name/label/fetch()
- 新增数据源 = 继承 BaseSource 实现 fetch()，注册到 sources/__init__.py 的 REGISTRY
"""
from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    """统一热点条目。heat 为各源原始热度（量纲不同，评分时按源内排名归一化）。"""
    source: str
    title: str
    url: str
    rank: int = 0
    heat: int = 0
    desc: str = ""
    tags: List[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        return d


def clean_text(s: str) -> str:
    """清洗文本：去 HTML 标签、空白压缩。"""
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


class BaseSource:
    """数据源基类。子类必须定义 name/label 并实现 fetch()。"""
    name: str = "base"
    label: str = "Base"
    weight: float = 1.0          # 源权重（评分用）
    limit: int = 20              # 每源最多抓取条数
    timeout: int = 15

    def fetch(self) -> List[Item]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<Source {self.name} label={self.label} weight={self.weight}>"
