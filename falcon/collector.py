"""采集调度器：遍历所有源 → 统一容错 → 汇总 + 运行状态。

设计要点：
- 单源失败不影响整体（记录 status 供监控层使用）
- 输出统一结构：{sources: {...}, items: [...], fetched_at, status}
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone, timedelta

from .sources import all_sources, source_labels

CST = timezone(timedelta(hours=8))


def collect(only: list[str] | None = None) -> dict:
    labels = source_labels()
    status: dict[str, dict] = {}
    items = []
    for src in all_sources(only):
        t0 = time.time()
        try:
            got = src.fetch()
            status[src.name] = {"ok": True, "count": len(got), "ms": int((time.time() - t0) * 1000)}
            for it in got:
                it.source = src.name  # 确保来源标记
                items.append(it.to_dict())
            print(f"[OK]   {src.name:<12} {src.label:<14} {len(got):>3} items  ({status[src.name]['ms']}ms)", file=sys.stderr)
        except Exception as e:
            status[src.name] = {"ok": False, "count": 0, "ms": int((time.time() - t0) * 1000), "error": f"{type(e).__name__}: {e}"}
            print(f"[FAIL] {src.name:<12} {src.label:<14} {type(e).__name__}: {e}", file=sys.stderr)
    ok_count = sum(1 for s in status.values() if s.get("ok"))
    return {
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "status": status,
        "ok_sources": ok_count,
        "total_sources": len(status),
        "source_labels": labels,
        "items": items,
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Falcon 采集层")
    ap.add_argument("--only", nargs="*", help="只采集指定源，如 --only weibo github")
    ap.add_argument("-o", "--out", default="data/raw.json", help="输出路径")
    args = ap.parse_args()

    data = collect(args.only)
    # 持久化到仓库 data/raw.json（供分析层/监控层使用）
    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"saved {args.out}: {len(data['items'])} items, {data['ok_sources']}/{data['total_sources']} sources OK")
    # 有源失败时返回非零（但不算致命错误，监控层会细看）
    return 0 if data["ok_sources"] >= max(1, data["total_sources"] // 2) else 2


if __name__ == "__main__":
    sys.exit(main())
