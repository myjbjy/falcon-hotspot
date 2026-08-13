#!/usr/bin/env python3
"""猎鹰监控看门狗（watchdog，no_agent 模式，零 LLM 成本）。

检查项：
1. 最新日报是否新鲜（data/daily/ 最新文件 < 30 小时）
2. 最新归档是否有数据（items > 0）
3. 采集成功源比例 >= 50%
4. 站点产物存在（site/index.html, site/latest.json, site/history.json）

报警策略（避免单次抖动骚扰）：
- 致命问题（0 条数据 / 无归档 / 站点产物缺失）→ 立即报警（exit 1）
- 非致命问题（源部分失败 / 日报略旧）→ 计入连续失败计数，连续 2 天才报警；
  单次抖动静默记录（exit 0），不打扰用户

退出码：0 = 正常/单次抖动；非 0 = 需要人工介入（cron no_agent 模式会发错误告警）。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.environ.get("FALCON_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY = os.path.join(ROOT, "data", "daily")
SITE = os.path.join(ROOT, "docs")
FAIL_MARK = os.path.join(ROOT, "data", ".fail_count")
CST = timezone(timedelta(hours=8))

fatal: list[str] = []
warn: list[str] = []


def check_freshness() -> None:
    if not os.path.isdir(DAILY) or not os.listdir(DAILY):
        fatal.append("data/daily 目录为空（从未成功跑过流水线）")
        return
    dates = sorted(f[:-5] for f in os.listdir(DAILY) if f.endswith(".json"))
    latest = dates[-1]
    try:
        mtime = os.path.getmtime(os.path.join(DAILY, latest + ".json"))
        age_h = (datetime.now(CST).timestamp() - mtime) / 3600
    except Exception:
        age_h = 999
    if age_h > 30:
        fatal.append(f"最新日报 {latest} 已 {age_h:.0f} 小时未更新（>30h）")


def check_content() -> None:
    dates = sorted(f[:-5] for f in os.listdir(DAILY)) if os.path.isdir(DAILY) else []
    if not dates:
        return
    try:
        with open(os.path.join(DAILY, dates[-1] + ".json"), encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        fatal.append(f"最新归档解析失败: {e}")
        return
    items = payload.get("items", [])
    if not items:
        fatal.append("最新归档 0 条数据（全部源失败）")
    ok = payload.get("ok_sources", 0)
    total = payload.get("total_sources", 0)
    if total and ok < max(1, total // 2):
        fails = [f"{n}: {s.get('error', '?')}" for n, s in (payload.get("status") or {}).items() if not s.get("ok")]
        warn.append(f"采集成功源 {ok}/{total} 低于阈值; 失败: {'; '.join(fails)}")


def check_site() -> None:
    for f in ("index.html", "latest.json", "history.json"):
        if not os.path.exists(os.path.join(SITE, f)):
            fatal.append(f"站点产物缺失: site/{f}")
    # 站点数据新鲜度：每 3 小时刷新一次，超过 4.5h 未更新视为异常
    lp = os.path.join(SITE, "latest.json")
    if os.path.exists(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get("fetched_at") or ""
            if ts:
                dt = datetime.fromisoformat(ts)
                age_h = (datetime.now(CST) - dt).total_seconds() / 3600
                if age_h > 4.5:
                    warn.append(f"站点数据已 {age_h:.1f} 小时未刷新（>4.5h，正常每 3h 一次）")
        except Exception as e:
            fatal.append(f"latest.json 解析失败: {e}")


def main() -> int:
    check_freshness()
    check_content()
    check_site()

    if fatal:
        print("FALCON WATCHDOG ALERT (fatal)")
        for p in fatal:
            print(f"  - {p}")
        return 1

    if warn:
        fail_count = 0
        try:
            with open(FAIL_MARK) as f:
                fail_count = int(f.read().strip() or 0)
        except Exception:
            pass
        fail_count += 1
        with open(FAIL_MARK, "w") as f:
            f.write(str(fail_count))
        if fail_count >= 2:
            print("FALCON WATCHDOG ALERT (连续异常)")
            for p in warn:
                print(f"  - {p}")
            print(f"  - 已连续 {fail_count} 天异常，请检查流水线")
            return 1
        # 单次抖动：静默
        return 0

    # 正常：清零计数，静默
    try:
        with open(FAIL_MARK, "w") as f:
            f.write("0")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
