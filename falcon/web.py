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
:root{
  --bg0:#04060e; --bg1:#0a0f22; --card:rgba(16,22,46,.55);
  --line:rgba(148,163,255,.14); --line2:rgba(148,163,255,.08);
  --text:#e9edfb; --dim:#8791b5; --dim2:#5d6a92;
  --blue:#4f8cff; --cyan:#22d3ee; --violet:#a78bfa; --pink:#f472b6; --amber:#fbbf24;
  --grad:linear-gradient(120deg,#4f8cff,#22d3ee 45%,#a78bfa);
  --mono:ui-monospace,'Cascadia Code',Consolas,'JetBrains Mono',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scrollbar-color:#2a3354 transparent}
body{
  font-family:'PingFang SC','Microsoft YaHei',-apple-system,'Segoe UI',sans-serif;
  background:var(--bg0);color:var(--text);min-height:100vh;overflow-x:hidden;
}
/* 深空背景：径向光斑 + 细网格 */
body::before{
  content:"";position:fixed;inset:0;z-index:-2;
  background:
    radial-gradient(600px 400px at 12% -5%,rgba(79,140,255,.16),transparent 65%),
    radial-gradient(700px 500px at 88% 8%,rgba(167,139,250,.13),transparent 60%),
    radial-gradient(800px 600px at 50% 110%,rgba(34,211,238,.09),transparent 60%),
    linear-gradient(180deg,#060a18 0%,#04060e 55%,#070b1a 100%);
}
body::after{
  content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background-image:
    linear-gradient(rgba(148,163,255,.045) 1px,transparent 1px),
    linear-gradient(90deg,rgba(148,163,255,.045) 1px,transparent 1px);
  background-size:44px 44px;
  mask-image:radial-gradient(ellipse 90% 70% at 50% 0%,#000 30%,transparent 100%);
}
header{padding:46px 22px 30px;position:relative;text-align:center}
.badge{
  display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:.78rem;
  color:var(--cyan);border:1px solid rgba(34,211,238,.35);border-radius:999px;
  padding:5px 14px;background:rgba(34,211,238,.07);letter-spacing:.06em;
}
.badge .dot{width:7px;height:7px;border-radius:50%;background:var(--cyan);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(34,211,238,.5)}50%{opacity:.6;box-shadow:0 0 0 6px rgba(34,211,238,0)}}
h1{
  margin:18px 0 10px;font-size:clamp(1.7rem,4vw,2.6rem);font-weight:800;letter-spacing:.01em;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;
  text-shadow:0 0 40px rgba(79,140,255,.25);
}
header .sub{color:var(--dim);font-size:.95rem}
header .sub b{color:var(--text);font-weight:600}
main{max-width:1080px;margin:0 auto;padding:0 20px 40px}
/* 统计条 */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:26px 0 30px}
.stat{
  position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 18px;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  overflow:hidden;transition:transform .25s,border-color .25s;
}
.stat:hover{transform:translateY(-3px);border-color:rgba(79,140,255,.4)}
.stat::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--c,var(--blue)),transparent);opacity:.8}
.stat .num{font-family:var(--mono);font-size:1.55rem;font-weight:700;
  background:linear-gradient(120deg,#fff,var(--c,var(--blue)));-webkit-background-clip:text;background-clip:text;color:transparent}
.stat .lab{color:var(--dim);font-size:.78rem;margin-top:3px;letter-spacing:.04em}
.card{
  background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px;
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);margin-bottom:18px;
  box-shadow:0 10px 40px rgba(3,6,20,.4);
}
.card h2{font-size:1.02rem;font-weight:700;display:flex;align-items:center;gap:9px;margin-bottom:4px}
.card h2 .ico{width:26px;height:26px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;
  background:rgba(79,140,255,.14);border:1px solid rgba(79,140,255,.3);font-size:.9rem}
.card .hint{color:var(--dim2);font-size:.8rem;margin:0 0 14px 35px}
/* 筛选胶囊 */
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px 35px}
.filters button{
  font-family:var(--mono);font-size:.78rem;color:var(--dim);background:rgba(148,163,255,.06);
  border:1px solid var(--line2);border-radius:999px;padding:5px 13px;cursor:pointer;
  transition:all .2s;letter-spacing:.02em;
}
.filters button:hover{color:var(--text);border-color:rgba(79,140,255,.45)}
.filters button.on{
  color:#04121a;font-weight:700;border-color:transparent;
  background:linear-gradient(120deg,#4f8cff,#22d3ee);
  box-shadow:0 0 18px rgba(34,211,238,.35);
}
/* 热点列表 */
.topic{display:flex;align-items:center;gap:14px;padding:12px 6px;border-bottom:1px solid var(--line2);transition:background .2s}
.topic:last-child{border-bottom:none}
.topic:hover{background:rgba(148,163,255,.04)}
.rk{
  min-width:34px;height:30px;display:flex;align-items:center;justify-content:center;
  font-family:var(--mono);font-weight:800;font-size:.95rem;border-radius:9px;color:var(--dim);
  background:rgba(148,163,255,.07);border:1px solid var(--line2);
}
.rk.r1{color:#0b0a02;background:linear-gradient(135deg,#ffd76a,#f59e0b);border-color:transparent;box-shadow:0 0 16px rgba(245,158,11,.4)}
.rk.r2{color:#0b0d14;background:linear-gradient(135deg,#e2e8f0,#94a3b8);border-color:transparent}
.rk.r3{color:#2a1206;background:linear-gradient(135deg,#fdba74,#c2713d);border-color:transparent}
.tt{flex:1;min-width:0}
.tt a{color:var(--text);text-decoration:none;font-size:.95rem;line-height:1.5;transition:color .15s}
.tt a:hover{color:var(--cyan)}
.tt .meta{display:flex;align-items:center;gap:8px;margin-top:4px;flex-wrap:wrap}
.src-tag{font-size:.68rem;padding:2px 9px;border-radius:999px;font-family:var(--mono);letter-spacing:.02em;
  background:var(--c,rgba(148,163,255,.12));color:var(--c2,#9aa5c9);border:1px solid color-mix(in srgb,var(--c,#94a3ff) 35%,transparent)}
.heatbar{flex:1;max-width:150px;height:5px;border-radius:99px;background:rgba(148,163,255,.1);overflow:hidden}
.heatbar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--blue),var(--cyan));width:0;transition:width .8s cubic-bezier(.2,.8,.2,1)}
.heat-txt{font-family:var(--mono);font-size:.75rem;color:var(--dim);min-width:56px;text-align:right}
/* 各源榜单 */
details{background:rgba(148,163,255,.04);border:1px solid var(--line2);border-radius:12px;margin-bottom:10px;overflow:hidden}
details summary{
  cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;
  padding:13px 16px;font-weight:600;font-size:.92rem;color:var(--text);transition:background .2s;
}
details summary::-webkit-details-marker{display:none}
details summary:hover{background:rgba(148,163,255,.07)}
details summary .cnt{font-family:var(--mono);font-size:.72rem;color:var(--dim2);font-weight:400}
details summary .arr{margin-left:auto;color:var(--dim2);transition:transform .25s;font-size:.8rem}
details[open] summary .arr{transform:rotate(90deg)}
details .body{padding:4px 16px 10px}
details .topic{padding:9px 4px}
/* 图表 */
.chart-wrap{position:relative}
.chart-wrap canvas{max-height:230px}
/* 页脚 */
footer{text-align:center;color:var(--dim2);font-size:.75rem;padding:26px 20px 34px;font-family:var(--mono);letter-spacing:.03em}
footer .logo{color:var(--dim);font-size:.85rem;margin-bottom:6px}
/* 响应式 */
@media(max-width:720px){
  .stats{grid-template-columns:repeat(2,1fr)}
  .heatbar{display:none}
  .filters,.card .hint{margin-left:0}
}
</style>
</head>
<body>
<header>
  <span class="badge"><span class="dot"></span>FALCON·HOTSPOT&nbsp;·&nbsp;<span id="okSrc">--/--</span> SOURCES ONLINE</span>
  <h1>🦅 猎鹰热点追踪</h1>
  <p class="sub" id="subtitle">多源热点聚合 · 实时追踪全网脉搏</p>
</header>
<main>
  <div class="stats" id="stats"></div>
  <div class="card">
    <h2><span class="ico">📈</span>近 7 天趋势</h2>
    <p class="hint">采集规模与跨源主题演化</p>
    <div class="chart-wrap"><canvas id="trend"></canvas></div>
  </div>
  <div class="card">
    <h2><span class="ico">🔥</span>全网跨源热点 <span class="hint" id="crossInfo" style="display:inline;margin:0"></span></h2>
    <p class="hint">同一事件在多源出现次数越多权重越高</p>
    <div class="filters" id="filters"></div>
    <div id="topics"></div>
  </div>
  <div class="card">
    <h2><span class="ico">📡</span>各源榜单</h2>
    <p class="hint">点击展开查看每个源的实时排行</p>
    <div id="sources"></div>
  </div>
</main>
<footer>
  <div class="logo">🦅 FALCON HOTSPOT</div>
  <span id="footer">由猎鹰系统自动生成 · 数据仅供研究参考</span>
</footer>
<script>
const fmtH = h => h>=100000000 ? (h/100000000).toFixed(1)+'亿' : h>=10000 ? (h/10000).toFixed(1)+'万' : (h||'');
const SRC_COLORS = {
  weibo:'#ff4d4f', zhihu:'#1772f6', tieba:'#3aa0ff', baidu:'#ff4525', toutiao:'#f04142',
  ithome:'#ff7a45', v2ex:'#7c8db0', hackernews:'#ff6600', github:'#a371f7', csdn:'#e0392f'
};
let DATA = null;
async function load(){
  const [latest, history] = await Promise.all([
    fetch('latest.json').then(r=>r.json()).catch(()=>null),
    fetch('history.json').then(r=>r.json()).catch(()=>[])
  ]);
  DATA = latest;
  if(!DATA){document.getElementById('topics').innerHTML='<p style="color:var(--dim)">暂无数据，等待流水线生成…</p>';return}
  render(history||[]);
}
function render(history){
  const s = DATA.stats||{}, labels = s.source_labels||{};
  document.getElementById('okSrc').textContent = s.ok_sources+'/'+s.total_sources;
  document.getElementById('subtitle').innerHTML = `多源热点聚合 · 更新于 <b>${(DATA.fetched_at||'').replace('T',' ').slice(0,16)}</b>`;
  // 统计条
  const stats = [
    {n:s.total_items||0, l:'今日采集', c:'var(--blue)'},
    {n:s.total_topics||0, l:'热点主题', c:'var(--cyan)'},
    {n:s.cross_source_topics||0, l:'跨源主题', c:'var(--violet)'},
    {n:s.ok_sources+'/'+s.total_sources, l:'在线数据源', c:'var(--amber)'}
  ];
  document.getElementById('stats').innerHTML = stats.map(x=>
    `<div class="stat" style="--c:${x.c}"><div class="num">${x.n}</div><div class="lab">${x.l}</div></div>`).join('');
  document.getElementById('crossInfo').textContent = `${s.cross_source_topics||0} 个事件同时出现在多个平台`;
  // 趋势图
  if(history.length){
    const h = history.slice(-7);
    const ctx = document.getElementById('trend').getContext('2d');
    const g1 = ctx.createLinearGradient(0,0,0,230); g1.addColorStop(0,'rgba(79,140,255,.35)'); g1.addColorStop(1,'rgba(79,140,255,0)');
    new Chart(ctx,{type:'line',data:{labels:h.map(e=>e.date.slice(5)),
      datasets:[
        {label:'采集条数', data:h.map(e=>e.total_items), borderColor:'#4f8cff', borderWidth:2.5,
         pointRadius:3, pointBackgroundColor:'#4f8cff', tension:.35, fill:true, backgroundColor:g1},
        {label:'跨源主题', data:h.map(e=>e.cross_source_topics), borderColor:'#a78bfa', borderWidth:2,
         pointRadius:3, pointBackgroundColor:'#a78bfa', tension:.35, borderDash:[5,4]}
      ]},
      options:{responsive:true, maintainAspectRatio:false,
        plugins:{legend:{labels:{color:'#8791b5',usePointStyle:true,pointStyle:'circle',boxWidth:8,padding:18}}},
        scales:{x:{ticks:{color:'#5d6a92'},grid:{color:'rgba(148,163,255,.06)'}},
                y:{ticks:{color:'#5d6a92'},grid:{color:'rgba(148,163,255,.06)'},beginAtZero:true}}}});
  }
  // 筛选器
  const allSrc = [...new Set(DATA.topics.flatMap(t=>t.sources))];
  const fb = document.getElementById('filters');
  const mkBtn = (name,label,on)=>{const b=document.createElement('button');b.textContent=label;b.className=on?'on':'';b.onclick=()=>{fb.querySelectorAll('button').forEach(x=>x.className='');b.className='on';showTopics(name)};return b};
  fb.appendChild(mkBtn('all','全部',true));
  allSrc.forEach(s=>fb.appendChild(mkBtn(s, labels[s]||s, false)));
  window.showTopics = filter=>{
    const box = document.getElementById('topics'); box.innerHTML='';
    const list = DATA.topics.filter(t=>filter==='all'||t.sources.includes(filter)).slice(0,30);
    if(!list.length){box.innerHTML='<p style="color:var(--dim);padding:10px 4px">该源暂无跨源主题</p>';return}
    const maxHeat = Math.max(...list.map(t=>t.heat_sum||0),1);
    list.forEach((t,i)=>{
      const div=document.createElement('div'); div.className='topic';
      const rk = i<3 ? `<div class="rk r${i+1}">${t.rank}</div>` : `<div class="rk">${t.rank}</div>`;
      const tags = t.sources.map(s=>{
        const c = SRC_COLORS[s]||'#94a3ff';
        return `<span class="src-tag" style="--c:${c}33;--c2:${c}">${labels[s]||s}</span>`;
      }).join('');
      const pct = Math.min(Math.round((t.heat_sum||0)/maxHeat*100),100);
      div.innerHTML = `${rk}<div class="tt"><a href="${t.url||'#'}" target="_blank" rel="noopener">${t.title}</a>
        <div class="meta">${tags}<span class="heat-txt">${fmtH(t.heat_sum)}</span></div></div>
        <div class="heatbar"><i style="width:${pct}%"></i></div>`;
      box.appendChild(div);
    });
  };
  showTopics('all');
  // 各源榜单
  const sb = document.getElementById('sources'); sb.innerHTML='';
  Object.entries(DATA.per_source||{}).forEach(([name, items])=>{
    const c = SRC_COLORS[name]||'#94a3ff';
    const d = document.createElement('details');
    let lis = items.slice(0,10).map((it,j)=>{
      const rk = j<3 ? `<div class="rk r${j+1}">${it.rank||j+1}</div>` : `<div class="rk">${it.rank||j+1}</div>`;
      return `<div class="topic">${rk}<div class="tt"><a href="${it.url||'#'}" target="_blank" rel="noopener">${it.title}</a></div><div class="heat-txt">${fmtH(it.heat)}</div></div>`;
    }).join('');
    d.innerHTML = `<summary><span style="width:8px;height:8px;border-radius:3px;background:${c};display:inline-block;box-shadow:0 0 8px ${c}"></span>${labels[name]||name}<span class="cnt">${items.length} 条</span><span class="arr">▶</span></summary><div class="body">${lis}</div>`;
    sb.appendChild(d);
  });
  document.getElementById('footer').textContent = `由猎鹰系统自动生成 · ${DATA.fetched_at||''} · 数据仅供研究参考`;
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

