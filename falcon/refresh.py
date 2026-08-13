"""高频刷新入口：每 3 小时采集并更新站点（不含 LLM 解读与日报归档）。

与每日流水线（falcon.pipeline）的区别：
- pipeline：采集 → 分析 → 归档 daily → 日报 md/html → 站点 → (agent 补 LLM 解读)
- refresh ：采集 → 分析 → 站点（latest.json + index.html）→ 部署

刷新零 LLM 成本（纯 Python），用于保持站点数据新鲜；
每日 09:10 的流水线仍负责归档、日报与 AI 解读。

用法: python -m falcon.refresh
退出码: 0=正常（≥50% 源成功）；2=全部源失败（供 cron 告警）
"""
from __future__ import annotations

import json
import sys

from . import analyzer, collector, storage, web


def run_refresh() -> dict:
    raw = collector.collect()
    if not raw["items"]:
        raise RuntimeError("采集失败：0 条数据（全部源失败）")
    analysis = analyzer.analyze(raw)
    date_str = storage.today()
    paths = web.generate(analysis, date_str, fetched_at=raw["fetched_at"])
    return {
        "date": date_str,
        "web": paths,
        "stats": analysis["stats"],
    }


def main() -> int:
    try:
        result = run_refresh()
        s = result["stats"]
        print(f"[REFRESH] {result['date']} {s['ok_sources']}/{s['total_sources']} 源 "
              f"{s['total_items']} 条 {s['total_topics']} 主题")
        return 0
    except Exception as e:
        print(f"[REFRESH FAIL] {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
