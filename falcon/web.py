"""Web 展示层：生成站点落地页（Chart.js 趋势图 + 今日热点 + 各源筛选）。

站点 = 纯静态（GitHub Pages 托管），数据来自 site/latest.json + site/history.json，
零后端零依赖，维护成本最低。
"""
from __future__ import annotations

import json
import os

from . import storage

PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🦅 猎鹰热点追踪</title>
<script src="https://cdn.bootcdn.net/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--accent:#ff6a00;--bg:#0f1115;--card:#1a1e26;--text:#e6e6e6;--dim:#8b93a3}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text)}
header{padding:28px 20px;background:linear-gradient(135deg,#1a1e26,#241a12);border-bottom:1px solid #2a2f3a}
header h1{margin:0;font-size:1.7em}
header .sub{color:var(--dim);margin-top:6px;font-size:.92em}
main{max-width:980px;margin:0 auto;padding:20px}
.chart-card,.card{background:var(--card);border-radius:12px;padding:18px;margin:14px 0;border:1px solid #262c37}
.chart-card h2,.card h2{margin:0 0 12px;font-size:1.1em;color:var(--accent)}
.topic{display:flex;align-items:flex-start;gap:12px;padding:10px 4px;border-bottom:1px solid #232936}
.topic:last-child{border-bottom:none}
.topic .rk{min-width:26px;font-weight:700;color:var(--accent);font-size:1.05em}
.topic .tt{flex:1}
.topic .tt a{color:var(--text);text-decoration:none}
.topic .tt a:hover{color:var(--accent)}
.topic .src{color:var(--dim);font-size:.8em;margin-top:3px}
.topic .heat{color:var(--dim);font-size:.85em;white-space:nowrap}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.filters button{background:#232936;color:var(--dim);border:1px solid #2f3644;border-radius:20px;padding:5px 14px;cursor:pointer;font-size:.85em}
.filters button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.meta{color:var(--dim);font-size:.85em;margin-top:10px}
.legend{color:var(--dim);font-size:.85em}
</style>
</head>
<body>
<header>
<h1>🦅 猎鹰热点追踪</h1>
<div class="sub" id="subtitle">多源热点聚合 · 每日自动更新</div>
</header>
<main>
<div class="chart-card"><h2>近 7 天趋势</h2><canvas id="trend" height="90"></canvas></div>
<div class="card">
<h2>🔥 全网跨源热点 <span class="legend" id="crossInfo"></span></h2>
<div class="filters" id="filters"></div>
<div id="topics"></div>
</div>
<div class="card"><h2>📡 各源榜单</h2><div id="sources"></div></div>
<div class="meta" id="footer"></div>
</main>
<script>
const fmtH = h => h >= 10000 ? (h/10000).toFixed(1)+'万' : (h || '');
let DATA = null;
async function load(){
  const [latest, history] = await Promise.all([
    fetch('latest.json').then(r=>r.json()),
    fetch('history.json').then(r=>r.json())
  ]);
  DATA = latest; render(history);
}
function render(history){
  const stats = DATA.stats||{}, labels = stats.source_labels||{};
  document.getElementById('subtitle').textContent =
    `更新于 ${DATA.date} · ${stats.total_items}条采集 · ${stats.total_topics}个主题 · 成功源 ${stats.ok_sources}/${stats.total_sources}`;
  document.getElementById('crossInfo').textContent = `（${stats.cross_source_topics} 个跨源主题）`;

  const ctx = document.getElementById('trend').getContext('2d');
  const h = history.slice(-7);
  new Chart(ctx, {type:'line', data:{labels:h.map(e=>e.date.slice(5)),
    datasets:[
      {label:'采集条数', data:h.map(e=>e.total_items), borderColor:'#ff6a00', tension:.3, yAxisID:'y'},
      {label:'跨源主题', data:h.map(e=>e.cross_source_topics), borderColor:'#4fc3f7', tension:.3, yAxisID:'y'}
    ]},
    options:{plugins:{legend:{labels:{color:'#8b93a3'}}},
      scales:{x:{ticks:{color:'#8b93a3'}},y:{ticks:{color:'#8b93a3'},beginAtZero:true}}}});

  const allSrc = [...new Set(DATA.topics.flatMap(t=>t.sources))];
  const fb = document.getElementById('filters');
  const mkBtn = (name,label,on)=> {const b=document.createElement('button');b.textContent=label;b.className=on?'on':'';b.onclick=()=>{fb.querySelectorAll('button').forEach(x=>x.className='');b.className='on';showTopics(name)};return b};
  fb.appendChild(mkBtn('all','全部',true));
  allSrc.forEach(s=>fb.appendChild(mkBtn(s, labels[s]||s, false)));

  window.showTopics = (filter)=>{
    const box = document.getElementById('topics'); box.innerHTML='';
    DATA.topics.filter(t=>filter==='all'||t.sources.includes(filter)).slice(0,30).forEach(t=>{
      const div=document.createElement('div'); div.className='topic';
      div.innerHTML = `<div class="rk">#${t.rank}</div><div class="tt"><a href="${t.url||'#'}" target="_blank" rel="noopener">${t.title}</a>
        <div class="src">${t.sources.map(s=>labels[s]||s).join(' · ')}</div></div>
        <div class="heat">${fmtH(t.heat_sum)}</div>`;
      box.appendChild(div);
    });
  };
  showTopics('all');

  const sb = document.getElementById('sources'); sb.innerHTML='';
  Object.entries(DATA.per_source||{}).forEach(([name, items])=>{
    const card = document.createElement('details'); card.style.marginBottom='10px';
    const lab = labels[name]||name;
    let lis = items.slice(0,10).map((it,i)=>`<div class="topic"><div class="rk">${it.rank||i+1}</div><div class="tt"><a href="${it.url||'#'}" target="_blank" rel="noopener">${it.title}</a></div><div class="heat">${fmtH(it.heat)}</div></div>`).join('');
    card.innerHTML = `<summary style="cursor:pointer;color:var(--accent);font-weight:600">${lab}（${items.length}）</summary>${lis}`;
    sb.appendChild(card);
  });
  document.getElementById('footer').textContent = `由 Falcon Hotspot 自动生成 · ${DATA.fetched_at || ''} · 数据仅供研究参考`;
}
load();
</script>
</body>
</html>
"""


def generate(analysis: dict, date_str: str) -> dict:
    """生成站点文件：index.html + latest.json（history.json 由 report 层维护）。"""
    latest = {
        "date": date_str,
        "fetched_at": None,  # 由 pipeline 回填
        "stats": analysis["stats"],
        "topics": analysis["topics"][:50],
        "per_source": {k: v[:20] for k, v in analysis["per_source"].items()},
    }
    index = storage.save_site_file("index.html", PAGE)
    latest_path = storage.save_site_json("latest.json", latest)
    return {"index": index, "latest": latest_path}
