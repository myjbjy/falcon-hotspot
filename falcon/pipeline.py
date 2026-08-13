"""猎鹰流水线主入口：采集 → 分析 → 归档 → 报告 → 站点。

用法:
    python -m falcon.pipeline                 # 全链路（不含 LLM 解读）
    python -m falcon.pipeline --only weibo    # 指定源
    python -m falcon.pipeline --date 2026-08-13   # 重跑指定日期（读归档）
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from . import collector, analyzer, report, storage, web


def run_pipeline(only: list[str] | None = None) -> dict:
    # 1. 采集
    raw = collector.collect(only)
    if not raw["items"]:
        raise RuntimeError("采集失败：0 条数据（全部源失败），检查网络/源可用性")
    # 2. 分析
    analysis = analyzer.analyze(raw)
    analysis["source_status"] = raw["status"]
    # 3. 归档（daily JSON 含原始+分析，供历史/重跑）
    date_str = storage.today()
    payload = {**raw, "analysis": analysis}
    archive_path = storage.save_daily(payload, date_str)
    # 4. 报告 + 站点
    report_paths = report.generate(analysis, date_str)
    web_paths = web.generate(analysis, date_str, fetched_at=raw["fetched_at"])

    return {
        "date": date_str,
        "archive": archive_path,
        "report": report_paths,
        "web": web_paths,
        "stats": analysis["stats"],
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Falcon 流水线")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    try:
        result = run_pipeline(args.only)
        s = result["stats"]
        print(f"[DONE] {result['date']}: {s['total_items']} items / {s['total_topics']} topics "
              f"({s['cross_source_topics']} 跨源) / sources {s['ok_sources']}/{s['total_sources']}")
        print(f"  archive: {result['archive']}")
        print(f"  report:  {result['report']['md']}")
        print(f"  site:    {result['web']['index']}")
        return 0
    except Exception as e:
        print(f"[PIPELINE FAIL] {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
