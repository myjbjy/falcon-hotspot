# 🦅 猎鹰热点追踪系统 (Falcon Hotspot)

**多源热点采集 → 跨源聚类评分 → AI 日报 → Web 可视化展示，全自动无人值守。**

一个完整的 Shell Engineering 第五形态示例：代码做骨架（Python 模块），Agent/Skill 做灵魂（LLM 解读 + 调度编排），产物是**附带网站的超级应用**。

- 线上站点：https://myjbjy.github.io/falcon-hotspot/
- 系统架构图：https://myjbjy.github.io/falcon-hotspot/architecture.html
- 每日日报：`docs/daily/YYYY-MM-DD.md`（自动生成）

## 架构（对应课程五形态分层）

```
┌─ 调度层 ─┐   Hermes cron（每日 09:10 流水线 / 09:40 watchdog 监控）
├─ 采集层 ─┤   falcon/sources/：7 个可插拔源（贴吧/百度/头条/IT之家/V2EX/HN/GitHub）
├─ 分析层 ─┤   falcon/analyzer.py：跨源聚类 + 排名加权评分（纯 Python，零 LLM 成本）
│            └ LLM 解读：Hermes agent 读聚合结果生成《今日热点简报》
├─ 报告层 ─┤   falcon/report.py：日报 md + 自包含 html + history.json
├─ 展示层 ─┤   falcon/web.py：Chart.js 趋势图 + 跨源热点 + 各源榜单（纯静态，零后端）
├─ 监控层 ─┤   scripts/watchdog.py：产物新鲜度/完整性检查（no_agent，零 LLM 成本）
├─ 报警层 ─┘   连续 2 天异常才报警，单次抖动静默（低维护，不骚扰）
└─ 产品层 ─┘   GitHub Pages 公开站点 + 历史趋势数据
```

## 快速开始

```bash
# 全链路（采集→分析→归档→日报→站点）
python -m falcon.pipeline

# 只看采集
python -m falcon.collector

# 监控检查（正常时静默，异常时输出并返回非零）
python scripts/watchdog.py

# 部署到 Pages
bash scripts/deploy.sh
```

## 目录结构

```
falcon/
├── collector.py        # 采集调度（单源失败不影响整体）
├── sources/            # 数据源（新增源 = 继承 BaseSource + 注册）
│   ├── base.py         # Item 统一结构 + 接口
│   ├── tieba.py        # 贴吧热议（JSON）
│   ├── baidu.py        # 百度热搜（HTML，TLS 重试）
│   ├── toutiao.py      # 头条热榜（JSON）
│   ├── ithome.py       # IT之家（HTML）
│   ├── v2ex.py         # V2EX（JSON）
│   ├── hackernews.py   # Hacker News（JSON，并行）
│   └── github_trending.py  # GitHub Trending（HTML，重试）
├── analyzer.py         # 跨源聚类 + 评分 + LLM prompt 构建
├── report.py           # 日报 md/html + history.json
├── web.py              # 站点落地页 + latest.json
└── storage.py          # 归档与站点文件管理
scripts/
├── deploy.sh           # 自动提交推送 Pages
└── watchdog.py         # 监控看门狗
data/daily/             # 每日归档 JSON（历史数据源）
docs/                   # 生成的站点（Pages 发布源 = /docs）
```

## 评分算法

跨源聚类（bigram Jaccard 相似度）→ 主题评分：

```
score = Σ(源权重 / 源内排名) × (1 + 0.5 × (跨源数 - 1))
```

跨源出现次数越多越可能是真热点；单源靠前则保留源内热度。纯 Python 实现，零 API 成本。

## 定时任务（Hermes cron 示例）

| 任务 | 时间 | 说明 |
| --- | --- | --- |
| 每日流水线 | 09:10 | agent 模式：跑 `python -m falcon.pipeline` + LLM 写今日解读，追加到日报 + 部署 |
| 每日监控 | 09:40 | no_agent 模式：`python scripts/watchdog.py`，异常才输出（零 LLM 成本） |

## 新增数据源（3 步）

1. 在 `falcon/sources/` 写一个继承 `BaseSource` 的类（实现 `fetch()` 返回 `Item` 列表）
2. 在 `falcon/sources/__init__.py` 注册
3. 重跑 `python -m falcon.pipeline` 验证

## 成本

- 采集/评分/报告/站点：**零成本**（纯 Python + 免费公开接口）
- LLM 解读：每日一次 deepseek flash 模型，约 **¥0.05/天**
- 托管：GitHub Pages 免费

## License

MIT
