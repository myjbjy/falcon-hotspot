"""存储层：按日期归档 raw 数据，管理每日产物。

目录约定（仓库根相对）：
- data/daily/YYYY-MM-DD.json   每日原始采集+分析结果（历史数据源，入 git 供站点趋势图使用）
- site/                         生成站点产物（index.html、latest.json、history.json、daily/*.html）
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
DATA_DIR = os.path.join(ROOT, "data")
DAILY_DIR = os.path.join(DATA_DIR, "daily")
# GitHub Pages 发布源固定为 /docs（Pages source 仅支持根目录或 /docs）
SITE_DIR = os.path.join(ROOT, "docs")


def today() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d")


def ensure_dirs() -> None:
    os.makedirs(DAILY_DIR, exist_ok=True)
    os.makedirs(SITE_DIR, exist_ok=True)
    os.makedirs(os.path.join(SITE_DIR, "daily"), exist_ok=True)


def save_daily(payload: dict, date_str: str | None = None) -> str:
    """归档当日完整结果（采集+分析），返回路径。"""
    ensure_dirs()
    d = date_str or today()
    path = os.path.join(DAILY_DIR, f"{d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return path


def load_daily(date_str: str) -> dict | None:
    path = os.path.join(DAILY_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_daily_dates() -> list[str]:
    """按日期倒序列出已有归档。"""
    if not os.path.isdir(DAILY_DIR):
        return []
    return sorted((f[:-5] for f in os.listdir(DAILY_DIR) if f.endswith(".json")), reverse=True)


def latest_daily() -> dict | None:
    dates = list_daily_dates()
    if not dates:
        return None
    return load_daily(dates[0])


def save_site_file(name: str, content: str) -> str:
    ensure_dirs()
    path = os.path.join(SITE_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_site_json(name: str, obj: dict | list) -> str:
    return save_site_file(name, json.dumps(obj, ensure_ascii=False, indent=1))
