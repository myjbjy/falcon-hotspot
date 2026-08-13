"""分析层：跨源聚类 + 热度评分（纯 Python，零 LLM 成本）。

算法（借鉴「本周新星」思路的跨源版）：
1. 标题归一化：去标点/停用词 → 统一形式
2. 跨源聚类：bigram Jaccard 相似度 > 阈值 视为同一主题
3. 评分：score = Σ(源权重/源内排名) × 跨源加成(1 + 0.5×(n-1))
   跨源出现次数多 → 更可能是真正的全网热点；单源靠前 → 源内热点

输出结构（写入 daily JSON）：
- sources: 各源榜单（原样）
- topics: 聚合热点列表（score 降序，含 sources 出现明细）
- stats: 统计信息（条数、跨源主题数、成功源数）
"""
from __future__ import annotations

import json
import re

STOPWORDS = set("的了是在有和与就不人都一个上也这那到说会要对很能没看我他她它"
                "中国美国日本韩国印度伊朗俄罗斯乌克兰以色列巴勒斯坦消息最新今天曝光"
                "官方网友回应记者报道公司发布上线正式确认宣布首次全球全国网友")
PUNCT = set("，。！？、；：""''（）【】《》…—·~@#$%^&*()[]{}|\\/<>+=_-")


def norm_title(title: str) -> str:
    """归一化标题：小写、去标点、去停用词、压缩空白。"""
    t = title.lower()
    t = "".join(ch for ch in t if ch not in PUNCT)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= 6:
        return t
    parts = [p for p in t.split() if p and p not in STOPWORDS] if " " in t else [c for c in t if c not in STOPWORDS]
    return "".join(parts) if parts else t


def _bigrams(s: str):
    return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def similar(a: str, b: str, threshold: float = 0.45) -> bool:
    """bigram Jaccard 相似度判定同主题。短标题放宽阈值。"""
    if not a or not b:
        return False
    if a == b:
        return True
    ga, gb = _bigrams(a), _bigrams(b)
    inter = len(ga & gb)
    if inter == 0:
        return False
    j = inter / len(ga | gb)
    if min(len(a), len(b)) <= 4:
        return j >= 0.6
    return j >= threshold


def cluster_items(items: list[dict], sources_cfg: dict) -> list[dict]:
    """把全部条目聚类成主题。返回 topics 列表。"""
    topics: list[dict] = []
    for it in items:
        nt = norm_title(it.get("title", ""))
        if not nt:
            continue
        merged = None
        for t in topics:
            if similar(t["norm"], nt):
                merged = t
                break
        if merged is None:
            merged = {"norm": nt, "title": it["title"], "url": it.get("url", ""),
                      "items": [], "sources": set(), "rank_sum": 0.0,
                      "heat_sum": 0, "min_rank": 999}
            topics.append(merged)
        merged["items"].append(it)
        merged["sources"].add(it.get("source", ""))
        w = sources_cfg.get(it.get("source", ""), 1.0)
        r = it.get("rank") or 20
        merged["rank_sum"] += w / r
        merged["heat_sum"] += int(it.get("heat") or 0)
        merged["min_rank"] = min(merged["min_rank"], r)
        # 保留出现次数最多的标题作为代表
        if it["title"] != merged["title"]:
            cnt = sum(1 for x in merged["items"] if x["title"] == it["title"])
            if cnt > sum(1 for x in merged["items"] if x["title"] == merged["title"]):
                merged["title"] = it["title"]

    # 计算最终分：跨源加成
    for t in topics:
        n = len(t["sources"])
        t["score"] = round(t["rank_sum"] * (1 + 0.5 * (n - 1)), 4)
        t["sources"] = sorted(t["sources"])
        t["source_count"] = n
        del t["norm"]
    topics.sort(key=lambda t: -t["score"])
    for i, t in enumerate(topics, 1):
        t["rank"] = i
    return topics


def analyze(raw: dict) -> dict:
    """raw.json → 分析结果（聚类 + 评分 + 统计）。"""
    labels = raw.get("source_labels", {})
    weights = {}
    # 权重从注册表读（避免硬编码散落）
    from .sources import REGISTRY
    for name, cls in REGISTRY.items():
        weights[name] = cls.weight
    items = raw.get("items", [])
    topics = cluster_items(items, weights)

    per_source = {}
    for it in items:
        per_source.setdefault(it["source"], []).append(it)

    stats = {
        "total_items": len(items),
        "total_topics": len(topics),
        "cross_source_topics": sum(1 for t in topics if t["source_count"] >= 2),
        "ok_sources": raw.get("ok_sources", 0),
        "total_sources": raw.get("total_sources", 0),
        "source_labels": labels,
    }
    return {"stats": stats, "topics": topics, "per_source": per_source}


def build_llm_prompt(analysis: dict, date_str: str) -> str:
    """给 LLM 的解读 prompt（供 Hermes agent 环节使用）。"""
    top = analysis["topics"][:12]
    lines = [f"今天是 {date_str}，以下是猎鹰系统采集的跨源热点分析数据："]
    lines.append("")
    lines.append("## 全网跨源热点 TOP12（score=跨源排名加权）")
    for t in top:
        srcs = "、".join(t["sources"])
        lines.append(f"{t['rank']}. [{t['title']}] 出现源: {srcs}({t['source_count']}个) score={t['score']}")
    lines.append("")
    lines.append("## 各源概况")
    for name, items in analysis["per_source"].items():
        top3 = "；".join(i["title"] for i in items[:3])
        lines.append(f"- {name}: {len(items)}条，Top3: {top3}")
    lines.append("")
    lines.append("请输出一份《今日热点简报》：")
    lines.append("1. 用 2-3 句话概括今天全网最值得关注的主题及原因")
    lines.append("2. 分「科技/财经/社会/国际」归类列出今日重点（每条带一句解读）")
    lines.append("3. 一句话点评开发者圈（GitHub/HN/V2EX）今天的热点")
    lines.append("4. 预测明天可能继续发酵的方向")
    lines.append("要求：客观、克制、不编造；直接输出简报正文，不要前言。")
    return "\n".join(lines)
