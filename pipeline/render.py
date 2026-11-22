"""Static dashboard page. Desktop-first layout that collapses cleanly on phones."""
from __future__ import annotations

import html
import json
import math

from . import config as C

ST = {"green": ("Normal", "g"), "amber": ("Watch", "a"), "red": ("Danger", "r"), "na": ("No data", "n"), "info": ("Info", "i"), "hist": ("Building history", "n")}

CSS = r"""
@font-face{font-family:"Archivo";src:url(fonts/archivo-wdth.woff2) format("woff2");font-weight:100 900;font-stretch:62% 125%;font-display:swap}
:root{
  --paper:#e9eef3; --surface:#ffffff; --sunk:#f3f6f9; --ink:#14202e; --ink2:#4a5868; --ink3:#7d8a99;
  --rule:#d3dae2; --blue:#1f5fbf; --blue-soft:#dbe6f6;
  --g:#1e8a4c; --a:#c98a00; --r:#c2362b; --n:#9aa6b3; --i:#1f5fbf;
  --g-soft:#e2f2e8; --a-soft:#fbf0d6; --r-soft:#f8e1df;
  --radius-l:14px; --radius-s:6px;
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0e141c; --surface:#151e29; --sunk:#1b2633; --ink:#e6ecf2; --ink2:#a9b6c4; --ink3:#748294;
  --rule:#263343; --blue:#6fa2f0; --blue-soft:#1d2d44;
  --g:#3fb873; --a:#e0a92a; --r:#e5635a; --n:#5d6b7b; --i:#6fa2f0;
  --g-soft:#173123; --a-soft:#3a2f12; --r-soft:#3d1d1b;
}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 "Archivo",system-ui,-apple-system,"Segoe UI",sans-serif;font-variation-settings:"wdth" 100;font-feature-settings:"tnum" 1}
a{color:var(--blue)}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
.num{font-variant-numeric:tabular-nums}
.cond{font-stretch:75%;font-variation-settings:"wdth" 75}

/* top bar */
.top{background:var(--ink);color:var(--paper)}
.top .wrap{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{font-weight:700;font-size:17px;letter-spacing:.01em}
.stamps{display:flex;gap:18px;font-size:12.5px;color:#b8c3cf;flex-wrap:wrap}
.stamps b{color:#fff;font-weight:600}
@media (prefers-color-scheme:dark){.top{background:#05090e}}

/* tabs */
nav{position:sticky;top:0;z-index:10;background:var(--paper);border-bottom:1px solid var(--rule)}
nav .wrap{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none}
nav a{flex:none;padding:13px 14px 11px;color:var(--ink2);text-decoration:none;font-weight:600;font-size:14px;border-bottom:3px solid transparent}
nav a:hover{color:var(--ink)}
nav a.on{color:var(--ink);border-bottom-color:var(--blue)}
nav a:focus-visible,svg.sp:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
section.tab{display:none;padding:28px 0 64px}section.tab .wrap>h2:first-child{margin-top:0}section.tab.on{display:block}

/* verdict */
.verdict{margin:4px 0 26px;max-width:860px}
.verdict h1{font-size:clamp(28px,4.2vw,44px);line-height:1.08;margin:0 0 10px;font-weight:800;font-stretch:80%;font-variation-settings:"wdth" 80;letter-spacing:-.01em}
.verdict p{margin:0;color:var(--ink2);font-size:16.5px;max-width:70ch}

h2{font-size:19px;font-weight:700;margin:36px 0 12px;letter-spacing:-.005em}
h2 small{font-weight:500;color:var(--ink3);font-size:13.5px;margin-left:8px}
h3{font-size:15px;font-weight:700;margin:20px 0 8px}
.muted{color:var(--ink3);font-size:13px}
.panel{background:var(--surface);border-radius:var(--radius-l);padding:18px 20px;box-shadow:0 0 0 1px var(--rule)}

/* scenarios */
.scen{display:grid;grid-template-columns:repeat(4,1fr);gap:0;background:var(--surface);border-radius:var(--radius-l);box-shadow:0 0 0 1px var(--rule);overflow:hidden}
.sc{padding:18px 20px 16px;border-left:1px solid var(--rule);display:flex;flex-direction:column;gap:6px;min-width:0}
.sc:first-child{border-left:0}
.sc.top{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.sc.top .an,.sc.top .ds,.sc.top .dl{color:#b8c3cf}
.sc .hd{display:flex;gap:8px;align-items:baseline}
.sc .lt{font-weight:800;font-size:13px;width:22px;height:22px;border-radius:50%;display:inline-grid;place-items:center;background:var(--sunk);color:var(--ink2);flex:none}
.sc.top .lt{background:var(--blue);color:#fff}
.sc .nm{font-weight:700;font-size:15px;line-height:1.25}
.sc .an{font-size:12.5px;color:var(--ink3)}
.sc .big{font-size:58px;line-height:1;font-weight:800;font-stretch:70%;font-variation-settings:"wdth" 70;margin-top:4px}
.sc .dl{font-size:12.5px;color:var(--ink3)}
.sc .ds{font-size:13px;color:var(--ink2);margin-top:auto}
.meter{height:6px;border-radius:3px;background:var(--sunk);position:relative;overflow:hidden}
.sc.top .meter{background:#2a3848}
.meter i{position:absolute;left:0;top:0;bottom:0;border-radius:3px}
.meter.ticks::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent calc(35% - 1px),var(--surface) calc(35% - 1px),var(--surface) 35%,transparent 35%,transparent calc(60% - 1px),var(--surface) calc(60% - 1px),var(--surface) 60%,transparent 60%)}
.sc.top .meter.ticks::after{background:linear-gradient(90deg,transparent calc(35% - 1px),var(--ink) calc(35% - 1px),var(--ink) 35%,transparent 35%,transparent calc(60% - 1px),var(--ink) calc(60% - 1px),var(--ink) 60%,transparent 60%)}

/* two column overview */
.cols{display:grid;grid-template-columns:5fr 7fr;gap:20px;margin-top:20px}
.layers{display:grid;grid-template-columns:minmax(120px,auto) 1fr 34px;gap:9px 12px;align-items:center;font-size:14px}
.layers .v{text-align:right;font-weight:700}
.alert-list{list-style:none;margin:0;padding:0}
.alert-list li{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:baseline;padding:7px 0;border-top:1px solid var(--rule);font-size:14px}
.alert-list li:first-child{border-top:0}
.alert-list .val{font-weight:700;white-space:nowrap}

/* status */
.st{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;color:var(--ink2);white-space:nowrap}
.st::before{content:"";width:9px;height:9px;border-radius:2px;background:var(--c,var(--n))}
.st.g{--c:var(--g)}.st.a{--c:var(--a)}.st.r{--c:var(--r)}.st.n{--c:var(--n)}.st.i{--c:var(--i);}
.st.i::before{border-radius:50%}

/* AI strip */
.chain{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:4px}
.lk{padding:12px 14px;border-left:1px solid var(--rule);position:relative}
.lk:first-child{border-left:0}
.lk .ln{font-weight:700;font-size:14px}
.lk .lr{font-size:26px;font-weight:800;font-stretch:75%;font-variation-settings:"wdth" 75;line-height:1.15}
.lk.hit .lr{color:var(--r)}
.lk .lm{font-size:12.5px;color:var(--ink3)}
.lk:not(:last-child)::after{content:"";position:absolute;right:-7px;top:50%;width:12px;height:12px;background:var(--surface);border-top:1px solid var(--rule);border-right:1px solid var(--rule);transform:translateY(-50%) rotate(45deg);z-index:1}
.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}
.pill{border-radius:var(--radius-s);padding:12px 14px;background:var(--sunk)}
.pill.bad{background:var(--r-soft)}
.pill b{display:block;font-size:14px;margin-bottom:2px}
.pill span{font-size:13px;color:var(--ink2)}
.lightbadge{display:inline-flex;align-items:center;gap:8px;font-weight:800;font-size:20px}
.lightbadge::before{content:"";width:16px;height:16px;border-radius:50%;background:var(--c)}

/* indicator rows */
.grp{background:var(--surface);border-radius:var(--radius-l);box-shadow:0 0 0 1px var(--rule);overflow:hidden}
.row{display:grid;grid-template-columns:minmax(220px,1.3fr) 150px minmax(160px,1fr) 92px;gap:16px;align-items:center;padding:12px 20px;border-top:1px solid var(--rule)}
.row:first-child{border-top:0}
.row.r{box-shadow:inset 3px 0 0 var(--r)}.row.a{box-shadow:inset 3px 0 0 var(--a)}
.row .nm{font-weight:600;font-size:14.5px;line-height:1.3}
.row .nt{font-size:12.5px;color:var(--ink3);margin-top:2px;line-height:1.35}
.row .vl{text-align:right}
.row .vl b{font-size:22px;font-weight:800;font-stretch:80%;font-variation-settings:"wdth" 80}
.row .vl u{text-decoration:none;font-size:12.5px;color:var(--ink3);margin-left:3px}
.row .vl div{font-size:12px;color:var(--ink3);white-space:nowrap}
.row .stc{text-align:right}
svg.sp{display:block;width:100%;height:34px;touch-action:none;overflow:visible}

/* tables */
.tbl{overflow-x:auto;background:var(--surface);border-radius:var(--radius-l);box-shadow:0 0 0 1px var(--rule)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:9px 12px;border-top:1px solid var(--rule);text-align:right;white-space:nowrap}
tr:first-child th{border-top:0}
th{color:var(--ink3);font-weight:600;font-size:12.5px;background:var(--sunk)}
th:first-child,td:first-child{text-align:left;white-space:normal;min-width:200px}
tr.cur td{background:var(--blue-soft);font-weight:700}
.neg{color:var(--r)}.pos{color:var(--g)}
.tag-active{display:inline-block;margin-left:6px;font-size:12px;font-weight:700;color:var(--r)}
.note{margin:10px 2px 0;color:var(--ink3);font-size:13px;max-width:90ch}
details summary{cursor:pointer;color:var(--ink2);font-size:13px;margin-top:10px}

/* guide */
.guide{max-width:780px}
.guide p,.guide li{font-size:15.5px;line-height:1.6;color:var(--ink)}
.guide .lead{font-size:18px;color:var(--ink2)}
.steps{counter-reset:s;list-style:none;padding:0;margin:0}
.steps li{counter-increment:s;position:relative;padding:0 0 14px 44px}
.steps li::before{content:counter(s);position:absolute;left:0;top:1px;width:28px;height:28px;border-radius:50%;background:var(--ink);color:var(--paper);display:grid;place-items:center;font-weight:800;font-size:14px}
.gl{display:grid;grid-template-columns:minmax(200px,1fr) 2fr;gap:0;background:var(--surface);border-radius:var(--radius-l);box-shadow:0 0 0 1px var(--rule);overflow:hidden;margin-bottom:8px}
.gl > div{padding:10px 16px;border-top:1px solid var(--rule);font-size:14px}
.gl > div:nth-child(-n+2){border-top:0}
.gl .k{font-weight:600}
.legend-row{display:flex;gap:18px;flex-wrap:wrap;margin:8px 0}

#tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--paper);font-size:12px;padding:4px 8px;border-radius:4px;display:none;z-index:20;white-space:nowrap}

@media (max-width:900px){
  .wrap{padding:0 16px}
  .scen{grid-template-columns:repeat(2,1fr)}
  .sc:nth-child(3){border-left:0}.sc:nth-child(n+3){border-top:1px solid var(--rule)}
  .cols{grid-template-columns:1fr}
  .pillars{grid-template-columns:1fr}
  .row{grid-template-columns:1fr auto;gap:6px 12px;padding:12px 16px}
  .row .spc{grid-column:1/-1;order:3}
  .row .stc{order:2;text-align:left}
  .row .vl{order:1;grid-row:1;grid-column:2}
  .row .info{grid-column:1;grid-row:1}
  .sc .big{font-size:46px}
  .row .stc .muted{display:inline;margin-left:8px}
}
@media (max-width:560px){
  .chain{grid-template-columns:repeat(2,1fr)}
  .lk:nth-child(3){border-left:0}.lk:nth-child(n+3){border-top:1px solid var(--rule)}
  .lk:nth-child(2)::after{display:none}
  .gl{grid-template-columns:1fr}.gl > div:nth-child(2){border-top:1px solid var(--rule)}
  .gl .k{border-top:1px solid var(--rule)}.gl .d{border-top:0;padding-top:0}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
const tabs=[...document.querySelectorAll('nav a')];
function show(t){tabs.forEach(a=>a.classList.toggle('on',a.dataset.t===t));
document.querySelectorAll('section.tab').forEach(s=>s.classList.toggle('on',s.id===t));}
tabs.forEach(a=>a.addEventListener('click',e=>{e.preventDefault();show(a.dataset.t);window.scrollTo(0,0);
try{history.replaceState(null,'','#'+a.dataset.t)}catch(_){}}));
const h=location.hash.slice(1);if(h&&document.getElementById(h))show(h);
document.querySelectorAll('[data-go]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();show(a.dataset.go);window.scrollTo(0,0)}));
const tip=document.getElementById('tip');
function mv(e){const s=e.currentTarget,r=s.getBoundingClientRect(),p=e.touches?e.touches[0]:e;
const v=s.dataset.v.split(','),d=s.dataset.d.split(','),n=v.length;
let i=Math.round((p.clientX-r.left)/r.width*(n-1));i=Math.max(0,Math.min(n-1,i));
if(v[i]===''){tip.style.display='none';return}
tip.textContent=d[i]+'   '+v[i];tip.style.display='block';
tip.style.left=Math.min(p.clientX+10,innerWidth-130)+'px';tip.style.top=(p.clientY-30)+'px';}
document.querySelectorAll('svg.sp').forEach(s=>{s.addEventListener('mousemove',mv);s.addEventListener('touchmove',mv,{passive:true});
['mouseleave','touchend'].forEach(ev=>s.addEventListener(ev,()=>tip.style.display='none'));});
"""


def esc(x) -> str:
    return html.escape(str(x))


def isnan(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def fmt(spec, v):
    if isnan(v):
        return "–"
    try:
        return spec["fmt"].format(v)
    except Exception:  # noqa: BLE001
        return f"{v:.2f}"


def status(s):
    lb, c = ST.get(s, ST["na"])
    return f'<span class="st {c}">{lb}</span>'


def sparkline(vals, dates, th=None, w=300, h=34):
    pts = [(i, v) for i, v in enumerate(vals) if not isnan(v)]
    if len(pts) < 2:
        return '<div class="muted">History still building</div>'
    ys = [v for _, v in pts]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1
    for t in th or ():
        if not isnan(t) and lo - span * 0.6 <= t <= hi + span * 0.6:
            lo, hi = min(lo, t), max(hi, t)
    if hi == lo:
        hi = lo + 1
    n = len(vals)
    X = lambda i: 1 + (w - 6) * i / max(1, n - 1)  # noqa: E731
    Y = lambda v: 3 + (h - 6) * (1 - (v - lo) / (hi - lo))  # noqa: E731
    d = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in pts)
    lines = ""
    for t, col in zip(th or (), ("var(--a)", "var(--r)")):
        if not isnan(t) and lo <= t <= hi:
            lines += f'<line x1="0" x2="{w}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="2 3" vector-effect="non-scaling-stroke"/>'
    li, lv = pts[-1]
    vs = ",".join("" if isnan(v) else f"{v:.4g}" for v in vals)
    return (f'<svg class="sp" tabindex="0" role="img" aria-label="1-year history" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'data-v="{vs}" data-d="{",".join(dates)}">{lines}'
            f'<path d="{d}" fill="none" stroke="var(--blue)" stroke-width="1.75" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>'
            f'<circle cx="{X(li):.1f}" cy="{Y(lv):.1f}" r="2.5" fill="var(--blue)"/></svg>')


def pct_cell(v, digits=1):
    if isnan(v):
        return "<td>–</td>"
    return f'<td class="{"neg" if v < 0 else "pos"}">{v:+.{digits}f}%</td>'


def num_cell(v, f="{:.1f}"):
    return "<td>–</td>" if isnan(v) else f"<td>{f.format(v)}</td>"


def stress_color(v):
    return "var(--r)" if v >= 60 else "var(--a)" if v >= 35 else "var(--g)"


# ---------------------------------------------------------------- verdict
HEAD = {
    "A": "Equities are panicking, but nothing has broken underneath",
    "B": "Markets are pricing an earnings-downgrade bear",
    "C": "Stress is moving from stocks into credit",
    "D": "Funding markets are under strain",
}


def verdict(D) -> tuple[str, str]:
    sc = D["scenarios"]["now"]
    g = D["groups"]
    top = max(sc, key=sc.get)
    if sc[top] < 35:
        h1 = "Stress is low across the board"
    else:
        h1 = HEAD[top]
    cr, fu = g.get("credit") or 0, g.get("funding") or 0
    if cr < 45 and fu < 45:
        sub = "Credit and funding markets have not confirmed it."
    elif cr >= 45 and fu >= 45:
        sub = "Both credit and funding markets are confirming the stress."
    else:
        sub = ("Credit" if cr >= 45 else "Funding") + " markets are starting to confirm it."
    ai = D.get("ai")
    if ai:
        sub += f" AI funding chain is {({'green': 'green', 'amber': 'amber', 'red': 'red'})[ai['light']]}, with contagion at link {ai['stage'] or 0:.0f} of 4."
    return h1 + ".", sub


# ---------------------------------------------------------------- building blocks
def ind_row(c):
    spec = C.IND_BY_ID[c["id"]]
    th = c.get("th") or (None, None)
    chg = c.get("chg_1w")
    chg_s = "" if chg is None else f"{'+' if chg >= 0 else '−'}{fmt(spec, abs(chg)).lstrip('+')} 1w"
    pct = "" if c.get("pct") is None else f"{c['pct']:.0f}th pctile"
    chg_s = chg_s.replace(" 1w", " this week")
    sub = "".join(f"<div>{esc(x)}</div>" for x in (chg_s, pct) if x)
    ths = "" if isnan(th[0]) else f"Watch {fmt(spec, th[0])}, danger {fmt(spec, th[1])}. "
    cls = {"red": "r", "amber": "a"}.get(c["status"], "")
    return (f'<div class="row {cls}"><div class="info"><div class="nm">{esc(spec["name"])}</div>'
            f'<div class="nt">{esc(ths)}{esc(spec["note"])}</div></div>'
            f'<div class="vl"><b>{fmt(spec, c["value"])}</b><u>{esc(spec["unit"])}</u>{sub}</div>'
            f'<div class="spc">{sparkline(c["spark"], c["spark_d"], th)}</div>'
            f'<div class="stc">{status(c["status"])}<div class="muted">{esc(c.get("asof") or "")}</div></div></div>')


def scen_strip(D):
    sc = D["scenarios"]
    top = max(sc["now"], key=sc["now"].get)
    out = ['<div class="scen">']
    for k, meta in C.SCENARIOS.items():
        v = sc["now"][k]
        d5 = sc["delta_5d"].get(k)
        dprev = sc["delta_prev"].get(k)
        dl = []
        if dprev is not None:
            dl.append(f"{dprev:+.0f} since last update")
        if d5 is not None:
            dl.append(f"{d5:+.0f} over 5 days")
        out.append(f'<div class="sc{" top" if k == top else ""}"><div class="hd"><span class="lt">{k}</span><span class="nm">{esc(meta["name"])}</span></div>'
                   f'<div class="an">Like {esc(meta["analog"])}</div><div class="big num">{v:.0f}</div>'
                   f'<div class="meter ticks"><i style="width:{v}%;background:{stress_color(v)}"></i></div>'
                   f'<div class="dl">{esc("; ".join(dl))}</div><div class="ds">{esc(meta["desc"])}</div></div>')
    out.append("</div>")
    return "".join(out)


def ai_block(ai, full=False):
    lc = {"green": "var(--g)", "amber": "var(--a)", "red": "var(--r)"}[ai["light"]]
    P = [f'<div class="panel"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">'
         f'<span class="lightbadge" style="--c:{lc}">{ai["light"].capitalize()}</span>'
         f'<span class="muted">{ai["n_bad"]} of 3 pillars failing; contagion at link {ai["stage"] or 0:.0f} of 4</span></div>']
    P.append('<div class="chain">')
    for l in ai["chain"]:
        r20 = "–" if l["r20"] is None else f'{l["r20"]:+.1f}%'
        r5 = "–" if l["r5"] is None else f'{l["r5"]:+.1f}%'
        dd = "–" if l["dd"] is None else f'{l["dd"]:.0f}%'
        P.append(f'<div class="lk{" hit" if l["hit"] else ""}"><div class="ln">{esc(l["name"])}</div><div class="lr num">{r20}</div>'
                 f'<div class="lm">20 days; cracks at {l["th"]:.0f}%</div><div class="lm">5 days {r5}; from high {dd}</div></div>')
    P.append("</div>")
    if full:
        P.append('<div class="pillars">')
        for k, nm in (("credit", "Credit alarm"), ("monetize", "Monetization at the source"), ("capex", "Capex surprise")):
            r = ai["reasons"][k]
            P.append(f'<div class="pill{" bad" if r else ""}"><b>{nm}</b><span>{esc("; ".join(r)) if r else "Not triggered"}</span></div>')
        P.append("</div>")
    P.append("</div>")
    return "".join(P)


# ---------------------------------------------------------------- page
def render(D: dict) -> str:
    cards = {c["id"]: c for c in D["cards"]}
    h1, sub = verdict(D)
    bt = D.get("bt") or {}
    an = bt.get("analogs") or {}

    # ---- overview
    ov = [f'<div class="verdict"><h1>{esc(h1)}</h1><p>{esc(sub)}</p></div>', scen_strip(D),
          '<p class="note">Scores run from 0 to 100 and measure how much stress matches each pattern. They are not probabilities. '
          '<a href="#guide" data-go="guide">How to read this</a></p>']
    lay = ['<div class="panel"><h3 style="margin-top:0">Stress by layer</h3><div class="layers">']
    for gk, gv in D["groups"].items():
        if gv is None:
            continue
        lay.append(f'<div>{esc(C.GROUP_NAMES[gk])}</div><div class="meter"><i style="width:{gv}%;background:{stress_color(gv)}"></i></div><div class="v num">{gv:.0f}</div>')
    lay.append("</div></div>")
    al = ['<div class="panel">']
    if D["transitions"]:
        al.append('<h3 style="margin-top:0">Changed since the last update</h3><ul class="alert-list">')
        for t in D["transitions"][:12]:
            spec = C.IND_BY_ID[t["id"]]
            al.append(f'<li>{status(t["to"])}<span>{esc(spec["name"])} <span class="muted">was {ST[t["from"]][0].lower()}</span></span><span class="val num">{fmt(spec, t["value"])}{esc(spec["unit"])}</span></li>')
        al.append("</ul>")
    order = ["funding", "credit", "aicredit", "xasset", "policy", "growth", "equity", "internals", "ai", "aichain", "asia", "tw"]
    reds = sorted([c for c in D["cards"] if c["status"] == "red"], key=lambda c: order.index(C.IND_BY_ID[c["id"]]["grp"]) if C.IND_BY_ID[c["id"]]["grp"] in order else 99)
    al.append(f'<h3 style="{"margin-top:0" if not D["transitions"] else ""}">In danger now <small class="muted">{len(reds)} indicators, slow-moving layers first</small></h3>')
    if reds:
        al.append('<ul class="alert-list">' + "".join(
            f'<li><span class="st r" aria-label="Danger"></span><span>{esc(C.IND_BY_ID[c["id"]]["name"])} <span class="muted">{esc(C.GROUP_NAMES[C.IND_BY_ID[c["id"]]["grp"]])}</span></span><span class="val num">{fmt(C.IND_BY_ID[c["id"]], c["value"])}{esc(C.IND_BY_ID[c["id"]]["unit"])}</span></li>'
            for c in reds[:12]) + "</ul>")
        if len(reds) > 12:
            al.append(f'<p class="muted" style="margin:8px 0 0">{len(reds) - 12} more are in danger; open the Global, US, AI or Taiwan tab to see them.</p>')
    else:
        al.append('<p class="muted">Nothing is past its danger line.</p>')
    al.append("</div>")
    ov.append(f'<div class="cols">{"".join(lay)}{"".join(al)}</div>')
    if D.get("ai"):
        ov.append(f'<h2>AI funding chain <small><a href="#ai" data-go="ai">Open the full view</a></small></h2>{ai_block(D["ai"])}')
    if an.get("matches"):
        ov.append('<h2>Closest days in history <small>and what the S&amp;P did next</small></h2><div class="tbl"><table>'
                  '<tr><th>Date</th><th>Distance</th><th>1 month</th><th>3 months</th><th>6 months</th><th>12 months</th><th>Worst drop in 6 months</th></tr>')
        for m in an["matches"][:6]:
            f = m["fwd"]
            ov.append(f'<tr><td>{m["date"]}</td>{num_cell(m["dist"], "{:.2f}")}' + "".join(pct_cell(f[k]) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr>")
        s = an["summary"]
        ov.append('<tr class="cur"><td>Median</td><td></td>' + "".join(pct_cell((s.get(k) or {}).get("median")) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr></table></div>"
                  '<p class="note">Matched on S&amp;P drawdown, VIX, credit spread, 10-year yield, dollar, gold and stock-bond correlation, across every day since 2000. Lower distance means more similar.</p>')

    # ---- indicator tabs
    secs = {}
    for sk in C.SECTIONS:
        parts = []
        for gk in C.GROUP_NAMES:
            ids = [s["id"] for s in C.IND if s["sec"] == sk and s["grp"] == gk]
            if not ids:
                continue
            gv = D["groups"].get(gk)
            gtxt = f"<small>layer stress {gv:.0f}</small>" if gv is not None else ""
            parts.append(f'<h2>{esc(C.GROUP_NAMES[gk])} {gtxt}</h2><div class="grp">' + "".join(ind_row(cards[i]) for i in ids if i in cards) + "</div>")
        secs[sk] = "".join(parts)

    ai = D.get("ai")
    if ai:
        top_ai = [f'<div class="verdict"><h1>AI funding chain is {ai["light"]}.</h1><p>Risk travels from the weakest balance sheets to the strongest. '
                  'Credit is the alarm, Anthropic’s earnings are the verdict, and hyperscalers’ 2027 capex guidance decides whether to back upstream or the hyperscalers.</p></div>',
                  ai_block(ai, full=True)]
        wn = (D.get("manual") or {}).get("weekly_note") or {}
        if wn.get("text"):
            top_ai.append(f'<h2>This week in the news <small>{esc(wn.get("date", ""))}</small></h2><div class="panel"><p style="margin:0;max-width:80ch">{esc(wn["text"])}</p></div>')
        Q = ['<h2>Credit signals from the news <small>updated weekly</small></h2><div class="tbl"><table><tr><th>Indicator</th><th>Value</th><th>As of</th><th>Light</th><th>Watch</th><th>Danger</th></tr>']
        for it in ai["b_layer"]:
            v = "–" if it.get("value") is None else f'{it["value"]:,}{esc(it["unit"])}'
            Q.append(f'<tr><td><b>{esc(it["name"])}</b><div class="muted">{esc(it.get("note", ""))}</div></td><td>{v}</td><td>{esc(it.get("date") or "–")}</td>'
                     f'<td>{status(it["status"])}</td><td>{it["amber"]}</td><td>{it["red"]}</td></tr>')
        Q.append('</table></div><p class="note">These have no free data feed. A weekly job reads the news and updates them; treat anything more than two weeks old as stale.</p>')
        Q.append('<h2>Quarterly earnings checklist</h2><div class="grp">')
        stl = {"pending": ("Pending", "n"), "ok": ("Met", "g"), "miss": ("Missed", "r")}
        for it in ai["checklist"]:
            lb, cc = stl.get(it.get("status", "pending"), stl["pending"])
            note = f'<div class="nt">{esc(it["note"])}</div>' if it.get("note") else ""
            Q.append(f'<div class="row" style="grid-template-columns:140px 1fr 90px"><div class="nm">{esc(it["co"])}</div><div>{esc(it["item"])}{note}</div><div class="stc"><span class="st {cc}">{lb}</span></div></div>')
        Q.append('</div><h2>Calendar</h2><div class="grp">')
        for ev in ai["calendar"]:
            dd = ev["days"]
            when = "Date to be set" if dd is None else ("Today" if dd == 0 else f"In {dd} days" if dd > 0 else "Yesterday")
            soon = dd is not None and 0 <= dd <= 14
            Q.append(f'<div class="row{" a" if soon else ""}" style="grid-template-columns:140px 1fr 120px"><div class="nm num">{esc(ev.get("date") or "TBD")}</div>'
                     f'<div>{esc(ev["event"])}{" <span class=muted>(approximate date)</span>" if ev.get("approx") and ev.get("date") else ""}</div><div class="stc muted">{when}</div></div>')
        Q.append("</div>")
        secs["ai"] = "".join(top_ai) + secs["ai"] + "".join(Q)

    # ---- backtest
    B = ['<div class="verdict"><h1>How past selloffs played out.</h1><p>Everything here is computed from real price, rate and spread history. '
         'Small samples are flagged; use these as context, not forecasts.</p></div>']
    ep = bt.get("episodes") or {}
    cur = ep.get("current")
    if cur:
        N = cur["days"]
        B.append(f'<h2>This selloff against past ones <small>all measured at trading day {N} after the S&amp;P peak</small></h2><div class="tbl"><table>'
                 '<tr><th>Episode</th><th>S&amp;P</th><th>VIX high</th><th>Baa spread chg</th><th>Gold</th><th>A</th><th>B</th><th>C</th><th>D</th><th>S&amp;P next 3M</th><th>Next 12M</th></tr>')
        sm = cur.get("scen_max") or {}
        B.append(f'<tr class="cur"><td>Now, from {cur["peak"].strftime("%Y-%m-%d")}</td>{pct_cell(cur["dd"])}{num_cell(cur.get("vix_max"))}{num_cell(cur.get("baa_chg"), "{:+.2f}")}{pct_cell(cur.get("gold_chg"))}'
                 + "".join(num_cell(sm.get(k), "{:.0f}") for k in "ABCD") + "<td>?</td><td>?</td></tr>")
        for e in ep["episodes"]:
            dn = e.get("dayN")
            if not dn:
                continue
            s2 = dn.get("scen_max") or {}
            af = e.get("afterN") or {}
            B.append(f'<tr><td>{esc(e["name"])} <span class="muted">{e["peak"].strftime("%Y-%m")}</span></td>{pct_cell(dn["dd"])}{num_cell(dn.get("vix_max"))}{num_cell(dn.get("baa_chg"), "{:+.2f}")}{pct_cell(dn.get("gold_chg"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + pct_cell(af.get("3M")) + pct_cell(af.get("12M")) + "</tr>")
        B.append("</table></div>")
    if ep.get("episodes"):
        B.append('<h2>Past selloffs, peak to trough</h2><div class="tbl"><table><tr><th>Episode</th><th>Max drop</th><th>Days to trough</th><th>Days to recover</th>'
                 '<th>VIX high</th><th>Baa chg</th><th>10Y chg</th><th>Dollar</th><th>Gold</th><th>TLT</th><th>TAIEX worst</th><th>A</th><th>B</th><th>C</th><th>D</th></tr>')
        for e in ep["episodes"]:
            s2 = e.get("scen_max") or {}
            B.append(f'<tr><td>{esc(e["name"])} <span class="muted">{e["peak"].strftime("%Y-%m")}</span></td>{pct_cell(e["dd"])}{num_cell(e["to_trough"], "{:.0f}")}{num_cell(e["recover"], "{:.0f}")}'
                     f'{num_cell(e.get("vix_max"))}{num_cell(e.get("baa_chg"), "{:+.2f}")}{num_cell(e.get("y10_chg"), "{:+.2f}")}{pct_cell(e.get("usd_chg"))}{pct_cell(e.get("gold_chg"))}{pct_cell(e.get("tlt_chg"))}{pct_cell(e.get("twii_dd"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + "</tr>")
        B.append('</table></div><p class="note">Days are trading days. A–D are the highest scenario scores the model would have shown at the time, a check on whether the scoring makes sense: D should be high in March 2020, C in 2008.</p>')
    rl = bt.get("rules") or []
    if rl:
        B.append('<h2>When this happened before, what came next</h2><div class="tbl"><table><tr><th>Condition</th><th>Times</th><th>1M median</th><th>3M median</th><th>6M median</th><th>12M median</th><th>Up after 12M</th><th>Worst drop in 6M (median)</th></tr>')
        for r in rl:
            g = lambda k, f="median": (r.get(k) or {}).get(f)  # noqa: E731
            act = '<span class="tag-active">Active now</span>' if r.get("active") and not r.get("baseline") else ""
            B.append(f'<tr><td>{esc(r["name"])}{act}<div class="muted">{esc(r.get("asset", ""))}</div></td><td>{r.get("n", 0)}</td>'
                     + pct_cell(g("1M")) + pct_cell(g("3M")) + pct_cell(g("6M")) + pct_cell(g("12M"))
                     + num_cell(g("12M", "pos"), "{:.0f}%") + pct_cell(g("maxDD6M")) + "</tr>")
        B.append('</table></div><p class="note">Each episode counts once (one-month cooldown after a trigger). Fewer than 5 cases is anecdotal. Taiwan margin conditions fill in as margin history is backfilled.</p>')
        B.append('<details><summary>Show the trigger dates for each condition</summary>' + "".join(
            f'<p class="muted"><b>{esc(r["name"])}</b>: {", ".join(r.get("dates") or []) or "none"}</p>' for r in rl if not r.get("baseline")) + "</details>")
    if an.get("matches"):
        labels = an["labels"]
        B.append('<h2>Historical analogs, feature by feature</h2><div class="tbl"><table><tr><th>Date</th>' + "".join(f"<th>{esc(v)}</th>" for v in labels.values()) + "</tr>")
        B.append(f'<tr class="cur"><td>Today ({an["asof"]})</td>' + "".join(num_cell(an["today"][k], "{:+.2f}") for k in labels) + "</tr>")
        for m in an["matches"]:
            B.append(f'<tr><td>{m["date"]}</td>' + "".join(num_cell(m["feat"][k], "{:+.2f}") for k in labels) + "</tr>")
        B.append("</table></div>")
    B.append(f'<h2>Data status</h2><div class="panel"><ul class="alert-list">' + "".join(f"<li><span></span><span class=muted>{esc(x)}</span><span></span></li>" for x in D["log"]) + "</ul></div>")

    tabs = [("ov", "Overview", "".join(ov)), ("global", "Global", secs["global"]), ("us", "US", secs["us"]),
            ("ai", "AI funding chain", secs["ai"]), ("tw", "Taiwan", secs["tw"]), ("bt", "Backtest", "".join(B)),
            ("guide", "How to read", guide_html(D))]
    nav = "".join(f'<a href="#{t}" data-t="{t}" class="{"on" if i == 0 else ""}">{n}</a>' for i, (t, n, _) in enumerate(tabs))
    body = "".join(f'<section class="tab{" on" if i == 0 else ""}" id="{t}"><div class="wrap">{c}</div></section>' for i, (t, _, c) in enumerate(tabs))
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Market Stress Monitor</title>'
            '<link rel="preload" href="fonts/archivo-wdth.woff2" as="font" type="font/woff2" crossorigin>'
            f'<style>{CSS}</style></head><body>'
            f'<div class="top"><div class="wrap"><div class="brand">Market Stress Monitor</div><div class="stamps num">'
            f'<span>Updated <b>{esc(D["updated"])}</b> Shanghai</span><span>US close <b>{esc(D["asof_us"])}</b></span><span>Taiwan close <b>{esc(D["asof_tw"])}</b></span></div></div></div>'
            f'<nav aria-label="Sections"><div class="wrap">{nav}</div></nav>{body}<div id="tip"></div><script>{JS}</script>'
            f'<script type="application/json" id="data">{json.dumps({"scenarios": D["scenarios"]["now"], "updated": D["updated"]})}</script></body></html>')


# ---------------------------------------------------------------- guide
def guide_html(D) -> str:
    sc = D["scenarios"]["now"]
    top = max(sc, key=sc.get)
    rows = []
    for sk, sname in C.SECTIONS.items():
        rows.append(f"<h3>{esc(sname)}</h3><div class='gl'>")
        for spec in [s for s in C.IND if s["sec"] == sk]:
            if spec["mode"] == "info":
                th = "No light; it shows direction, not stress."
            elif spec["mode"] == "pct":
                th = f"Lights by its own history: watch past the {spec['amber'] * 100:.0f}th percentile, danger past the {spec['red'] * 100:.0f}th (or below the {spec['amber'] * 100:.0f}th/{spec['red'] * 100:.0f}th when low is bad)."
            else:
                worse = "higher" if spec["dir"] > 0 else "lower"
                th = f"Watch at {fmt(spec, spec['amber'])}{spec['unit']}, danger at {fmt(spec, spec['red'])}{spec['unit']} ({worse} is worse)."
            rows.append(f"<div class='k'>{esc(spec['name'])}</div><div class='d'>{esc(spec['note'] or '')}{' ' if spec['note'] else ''}<span class='muted'>{esc(th)}</span></div>")
        rows.append("</div>")
    return f"""<div class="guide">
<div class="verdict"><h1>How to read this dashboard.</h1>
<p class="lead">It answers one question twice a day: how worried should I be, and is it getting better or worse? Everything else is the evidence behind that answer.</p></div>

<h2>Reading it in a minute</h2>
<ol class="steps">
<li><b>Read the headline.</b> It names the pattern the data matches best right now (today: scenario {top}) and says whether credit and funding markets agree. Equity stress alone usually fades; stress that spreads into credit and funding is what turns a correction into a crisis.</li>
<li><b>Look at the four scenario scores and which way they moved.</b> The dark tile is the highest. The change since the last update and over five days matters more than the level: a score climbing 15 points in a week is the warning.</li>
<li><b>Scan "Changed since the last update".</b> These are the indicators that just crossed a line. This list is the reason to open the dashboard at all on a quiet day.</li>
<li><b>Check the AI funding chain.</b> If contagion is spreading link by link and the credit pillar turns red, the AI selloff is becoming a balance-sheet problem rather than a valuation problem.</li>
<li><b>Only then dig into a tab.</b> Global, US, AI and Taiwan list every indicator with its one-year line; Backtest shows what happened after similar setups.</li>
</ol>

<h2>The lights</h2>
<div class="legend-row"><span class="st g">Normal</span><span class="st a">Watch</span><span class="st r">Danger</span><span class="st i">Info</span><span class="st n">No data</span></div>
<p>Every indicator has a watch line and a danger line, shown as dashed amber and red lines on its chart. Fixed lines are anchored to past episodes (for example, the high-yield spread peaked near 5.3% in late 2018 and near 11% in March 2020). Indicators marked as percentile-based are judged against their own history, using only the data that existed at each point in time.</p>
<p>A single red light is not a signal. Look for several lights in the same layer turning together, and for lights in a slower layer (credit, funding) following a fast one (equities).</p>

<h2>Layer stress</h2>
<p>Each layer averages the stress of its indicators on a 0–100 scale: 0 is calm, 50 sits right on the watch line, 100 means everything is past danger. Equities, volatility and Asia move first and fastest. Credit and funding move slowly and rarely, which is why they carry more weight when they do move.</p>

<h2>The four scenarios</h2>
<p><b>A. Deleveraging correction</b> (like late 2018 or August 2024). Equities panic while credit and funding stay calm. Historically repaired within months. The score falls if credit or funding stress rises, because then it is no longer this pattern.</p>
<p><b>B. Earnings-downgrade bear</b> (like 2000). AI stocks fall, policy is tight and growth slows. This is the slow, multi-year path. It gets a bump if a hyperscaler announces a capex cut.</p>
<p><b>C. Credit event</b> (like mid-2007 or SVB in 2023). Stress spreads from equity into borrowers and lenders: high-yield and BBB spreads, private credit, regional banks, AI-linked debt.</p>
<p><b>D. Liquidity crisis</b> (like September 2008 or March 2020). Everything is sold at once, even Treasuries; the dollar spikes; repo rates jump above the Fed's rate.</p>
<p>The scores measure how strongly today's data matches each pattern. They are not probabilities and do not add up to 100. The weights are judgment calls, not statistically fitted; the Backtest tab shows the score each past episode would have produced so you can check them.</p>

<h2>Three switches that would change the view</h2>
<ol class="steps">
<li><b>Hyperscalers cut capex.</b> Watch the AI funding chain tab and the earnings checklist. This moves the story from valuation to earnings, toward scenario B.</li>
<li><b>Credit confirms.</b> High-yield spread above 4.5% or BBB above 2%, private credit underperforming, CoreWeave or Oracle CDS making new highs. This moves toward scenario C.</li>
<li><b>Treasuries and stocks fall together, the dollar spikes, SOFR jumps above IORB.</b> The "stocks/bonds/gold down together" and funding rows catch this. This is scenario D, and the one that forces central banks to act.</li>
</ol>

<h2>The AI funding chain</h2>
<p>Risk is assumed to travel from the weakest balance sheets to the strongest: neoclouds such as CoreWeave, then Oracle, then Nvidia and memory makers, then the cash-rich hyperscalers. A link counts as cracked when its 20-day return falls below its trigger, and only if every link before it has cracked too. Spreading in order means contagion; the hyperscalers falling while upstream holds is a different story.</p>
<p>The composite light has three pillars: the credit alarm, monetization at the source (Anthropic and peers against the earnings checklist), and capex surprises. One failing is amber. Two or more failing together is red, because a single negative rarely breaks the chain on its own.</p>
<p>The news-based credit signals (CDS, bond yields, GPU loan rates, H100 rental prices) have no free data feed, so a weekly job reads the news and updates them every Sunday.</p>

<h2>Taiwan</h2>
<p>Margin data shows forced selling. When margin calls hit, investors sell what they can, so locked limit-down small caps push selling into TSMC and the ETFs. The <i>deleveraging progress</i> row divides the fall in margin loans by the fall in the index since its peak; above 1 means leverage is being cut faster than prices are falling, which has tended to come near the end of a selloff (the Backtest tab tests this once enough history is loaded). The maintenance ratio here is an estimate on a different basis from brokers' figures, so read its direction rather than its level.</p>

<h2>Backtest and analogs</h2>
<p>The comparison table lines up every past selloff at the same number of trading days after its peak as today, so you are comparing like with like. The conditional table asks: the last times this exact condition was true, what did the market do over the following months? The analog table finds the days since 2000 whose overall picture (drawdown, VIX, credit, rates, dollar, gold, stock-bond correlation) looked most like today.</p>
<p>Samples are small: there have only been about a dozen major selloffs since 1998. Use these to calibrate expectations, not to forecast.</p>

<h2>Every indicator</h2>
{''.join(rows)}

<h2>Limits</h2>
<p>FRED only keeps about three years of the ICE high-yield, investment-grade and BBB spreads, so long backtests use Moody's Baa spread instead. Taiwan margin history is backfilled a little on every run and will be complete in about two weeks. Prices come from Yahoo Finance, which occasionally rate-limits; a missing ticker retries on the next run and shows as stale. This is a monitoring tool, not investment advice.</p>
</div>"""


METHOD_HTML = ""
