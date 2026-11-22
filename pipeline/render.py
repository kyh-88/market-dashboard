"""Static, mobile-first HTML dashboard (no external dependencies)."""
from __future__ import annotations

import html
import json
import math

from . import config as C

ST_LABEL = {"green": ("●", "Normal"), "amber": ("▲", "Watch"), "red": ("■", "Danger"), "na": ("○", "No data"), "info": ("◆", "Info")}

CSS = """
:root{--bg:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--line:#e6e5e0;
--series:#2a78d6;--good:#0ca30c;--warn:#fab219;--crit:#d03b3b;--chip:#f3f2ee}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--card:#232322;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#8f8e86;
--line:#383835;--series:#3987e5;--chip:#2d2d2b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header{padding:16px 16px 8px}h1{font-size:19px;margin:0}.sub{color:var(--ink2);font-size:12px}
nav{position:sticky;top:0;z-index:5;background:var(--bg);display:flex;gap:6px;padding:8px 12px;overflow-x:auto;border-bottom:1px solid var(--line)}
nav a{white-space:nowrap;text-decoration:none;color:var(--ink2);padding:6px 12px;border-radius:999px;background:var(--chip);font-size:13px}
nav a.on{background:var(--ink);color:var(--bg)}
section{display:none;padding:12px}section.on{display:block}
h2{font-size:16px;margin:18px 4px 8px}h3{font-size:14px;margin:14px 4px 6px;color:var(--ink2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.ind .top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.ind .nm{font-size:13px;color:var(--ink2)}.ind .val{font-size:20px;font-weight:600;font-variant-numeric:tabular-nums}
.ind .meta{font-size:11px;color:var(--ink3);margin-top:2px}.ind .note{font-size:11px;color:var(--ink3);margin-top:4px}
.chip{font-size:11px;padding:2px 7px;border-radius:999px;white-space:nowrap;border:1px solid var(--line);color:var(--ink2)}
.chip .ic{margin-right:3px}.s-green .ic{color:var(--good)}.s-amber .ic{color:var(--warn)}.s-red .ic{color:var(--crit)}
.card.s-red{border-left:4px solid var(--crit)}.card.s-amber{border-left:4px solid var(--warn)}
svg.sp{display:block;width:100%;height:36px;margin-top:6px;touch-action:none}
.scen{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.scen .card.top1{outline:2px solid var(--ink)}.scen .sc{font-size:28px;font-weight:700;font-variant-numeric:tabular-nums}
.scen .nm{font-weight:600}.scen .an{font-size:11px;color:var(--ink3)}.scen .ds{font-size:12px;color:var(--ink2);margin-top:4px}
.bar{height:8px;border-radius:4px;background:var(--chip);overflow:hidden;margin-top:6px}.bar i{display:block;height:100%;border-radius:4px}
.heat{display:grid;grid-template-columns:110px 1fr 36px;gap:6px 8px;align-items:center;font-size:13px}
.heat .n{color:var(--ink2)}.heat .v{text-align:right;font-variant-numeric:tabular-nums}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--card);white-space:normal;min-width:150px;max-width:190px}th{color:var(--ink2);font-weight:500}
tr.cur td{font-weight:700}.neg{color:var(--crit)}.pos{color:var(--good)}
ul.alerts{margin:0;padding-left:18px}ul.alerts li{margin:3px 0}
.muted{color:var(--ink3);font-size:12px}.legend{font-size:12px;color:var(--ink2);margin:4px}
#tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--bg);font-size:11px;padding:3px 6px;border-radius:4px;display:none;z-index:9}
.active{color:var(--crit);font-weight:600}
.chain{display:flex;gap:4px;align-items:stretch;overflow-x:auto}.chain .lk{flex:1;min-width:64px;border:1px solid var(--line);border-radius:8px;padding:6px;text-align:center;font-size:12px}
.chain .lk.hit{border-color:var(--crit);border-width:2px}.chain .ar{align-self:center;color:var(--ink3)}
.chain .lk b{display:block;font-size:12px;hyphens:manual}.big{font-size:22px;font-weight:700}
.pill{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;font-size:13px;margin-top:8px}
"""

JS = """
document.querySelectorAll('nav a').forEach(a=>a.onclick=e=>{e.preventDefault();
document.querySelectorAll('nav a,section').forEach(x=>x.classList.remove('on'));a.classList.add('on');
document.getElementById(a.dataset.t).classList.add('on');window.scrollTo(0,0);try{history.replaceState(null,'','#'+a.dataset.t)}catch(_){}} );
const h=location.hash.slice(1);if(h){const a=document.querySelector('nav a[data-t="'+h+'"]');if(a)a.click();}
const tip=document.getElementById('tip');
function mv(e){const s=e.currentTarget,r=s.getBoundingClientRect();const p=e.touches?e.touches[0]:e;
const v=s.dataset.v.split(','),d=s.dataset.d.split(','),n=v.length;let i=Math.round((p.clientX-r.left)/r.width*(n-1));i=Math.max(0,Math.min(n-1,i));
tip.textContent=d[i]+'  '+v[i];tip.style.display='block';tip.style.left=Math.min(p.clientX+8,innerWidth-120)+'px';tip.style.top=(p.clientY-28)+'px';}
document.querySelectorAll('svg.sp').forEach(s=>{s.addEventListener('mousemove',mv);s.addEventListener('touchmove',mv,{passive:true});
s.addEventListener('mouseleave',()=>tip.style.display='none');s.addEventListener('touchend',()=>tip.style.display='none');});
"""


def esc(x) -> str:
    return html.escape(str(x))


def fmt(spec, v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    try:
        return spec["fmt"].format(v)
    except Exception:  # noqa: BLE001
        return f"{v:.2f}"


def sparkline(vals, dates, th=None, w=300, h=36):
    pts = [(i, v) for i, v in enumerate(vals) if v is not None and not math.isnan(v)]
    if len(pts) < 2:
        return '<div class="muted">History still accumulating</div>'
    ys = [v for _, v in pts]
    lo, hi = min(ys), max(ys)
    if th:
        for t in th:
            if t is not None and not math.isnan(t) and lo - (hi - lo) * 0.5 <= t <= hi + (hi - lo) * 0.5:
                lo, hi = min(lo, t), max(hi, t)
    if hi == lo:
        hi = lo + 1
    n = len(vals)
    X = lambda i: 2 + (w - 4) * i / max(1, n - 1)  # noqa: E731
    Y = lambda v: 3 + (h - 6) * (1 - (v - lo) / (hi - lo))  # noqa: E731
    d = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in pts)
    lines = ""
    if th:
        for t, col in zip(th, ("var(--warn)", "var(--crit)")):
            if t is not None and not math.isnan(t) and lo <= t <= hi:
                lines += f'<line x1="0" x2="{w}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="3 3"/>'
    li, lv = pts[-1]
    vs = ",".join("" if v is None or math.isnan(v) else f"{v:.4g}" for v in vals)
    return (f'<svg class="sp" viewBox="0 0 {w} {h}" preserveAspectRatio="none" data-v="{vs}" data-d="{",".join(dates)}">'
            f'{lines}<path d="{d}" fill="none" stroke="var(--series)" stroke-width="2" vector-effect="non-scaling-stroke"/>'
            f'<circle cx="{X(li):.1f}" cy="{Y(lv):.1f}" r="3" fill="var(--series)"/></svg>')


def chip(status):
    ic, lb = ST_LABEL[status]
    return f'<span class="chip s-{status}"><span class="ic">{ic}</span>{lb}</span>'


def ind_card(c):
    spec = C.IND_BY_ID[c["id"]]
    chg = c.get("chg_1w")
    chg_s = "" if chg is None else f"1w chg {'+' if chg >= 0 else '−'}{fmt(spec, abs(chg)).lstrip('+')}"
    pct = "" if c.get("pct") is None else f"{c['pct']:.0f}th pctile"
    th = c.get("th") or (None, None)
    ths = "" if th[0] is None or (isinstance(th[0], float) and math.isnan(th[0])) else \
        f"Watch {fmt(spec, th[0])} / Danger {fmt(spec, th[1])}"
    meta = " · ".join(x for x in (chg_s, pct, f"as of {c['asof']}" if c.get("asof") else "") if x)
    return (f'<div class="card ind s-{c["status"]}"><div class="top"><div><div class="nm">{esc(spec["name"])}</div>'
            f'<div class="val">{fmt(spec, c["value"])}<span class="muted"> {esc(spec["unit"])}</span></div></div>{chip(c["status"])}</div>'
            f'{sparkline(c["spark"], c["spark_d"], th)}<div class="meta">{esc(meta)}</div>'
            f'<div class="note">{esc(ths)}{" · " if ths and spec["note"] else ""}{esc(spec["note"])}</div></div>')


def pct_cell(v, digits=1):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "<td>—</td>"
    cls = "neg" if v < 0 else "pos"
    return f'<td class="{cls}">{v:+.{digits}f}</td>'


def num_cell(v, f="{:.1f}"):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "<td>—</td>"
    return f"<td>{f.format(v)}</td>"


def render(D: dict) -> str:
    cards = {c["id"]: c for c in D["cards"]}
    sc = D["scenarios"]
    top = max(sc["now"], key=sc["now"].get)
    # ---------------- overview
    ov = ['<h2>Scenarios</h2><div class="scen">']
    for k, meta in C.SCENARIOS.items():
        v = sc["now"][k]
        d_prev = sc["delta_prev"].get(k)
        d5 = sc["delta_5d"].get(k)
        col = "var(--crit)" if v >= 60 else "var(--warn)" if v >= 35 else "var(--good)"
        dtxt = " · ".join(x for x in (f"vs last {d_prev:+.0f}" if d_prev is not None else "",
                                       f"5d {d5:+.0f}" if d5 is not None else "") if x)
        ov.append(f'<div class="card{" top1" if k == top else ""}"><div class="nm">{k}. {esc(meta["name"])}</div>'
                  f'<div class="an">Analog: {esc(meta["analog"])}</div><div class="sc">{v:.0f}</div>'
                  f'<div class="bar"><i style="width:{v}%;background:{col}"></i></div>'
                  f'{sparkline(sc["hist"][k], sc["hist_d"], None)}<div class="muted">{esc(dtxt)}</div>'
                  f'<div class="ds">{esc(meta["desc"])}</div></div>')
    ov.append('</div><p class="legend">Scores run 0–100 and are weighted from layer stress (formulas under Method on the Backtest tab). They measure relative stress, not probability.</p>')
    if D.get("ai"):
        ai0 = D["ai"]
        lb0 = {"green": "Green", "amber": "Amber", "red": "Red"}[ai0["light"]]
        ov.append(f'<div class="card s-{ai0["light"]}" style="margin-top:8px"><b>AI funding chain: {chip(ai0["light"]).replace(ST_LABEL[ai0["light"]][1], lb0)}</b> '
                  f'{ai0["n_bad"]}/3 pillars failing · contagion at link {ai0["stage"] or 0:.0f}/4 <span class="muted">(see AI funding chain tab)</span></div>')
    ov.append('<h2>Stress by layer</h2><div class="card heat">')
    for gk, gv in D["groups"].items():
        if gv is None:
            continue
        col = "var(--crit)" if gv >= 70 else "var(--warn)" if gv >= 45 else "var(--good)"
        ov.append(f'<div class="n">{esc(C.GROUP_NAMES[gk])}</div><div class="bar" style="margin:0"><i style="width:{gv}%;background:{col}"></i></div><div class="v">{gv:.0f}</div>')
    ov.append("</div>")
    ov.append('<h2>Changes and alerts</h2><div class="card">')
    if D["transitions"]:
        ov.append('<h3 style="margin-top:0">Changed since last update</h3><ul class="alerts">' + "".join(
            f'<li>{chip(t["to"])} {esc(C.IND_BY_ID[t["id"]]["name"])}: {fmt(C.IND_BY_ID[t["id"]], t["value"])} (was {ST_LABEL[t["from"]][1]})</li>'
            for t in D["transitions"]) + "</ul>")
    reds = [c for c in D["cards"] if c["status"] == "red"]
    ov.append('<h3>Currently in danger</h3>' + ('<ul class="alerts">' + "".join(
        f'<li>{esc(C.IND_BY_ID[c["id"]]["name"])}: <b>{fmt(C.IND_BY_ID[c["id"]], c["value"])}</b> {esc(C.IND_BY_ID[c["id"]]["unit"])}</li>' for c in reds)
        + "</ul>" if reds else '<div class="muted">None</div>'))
    ov.append("</div>")
    an = (D.get("bt") or {}).get("analogs") or {}
    if an.get("matches"):
        ov.append('<h2>Most similar days in history</h2><div class="card tbl"><table><tr><th>Date</th><th>Distance</th><th>Next 1M</th><th>3M</th><th>6M</th><th>12M</th><th>Max DD in 6M</th></tr>')
        for m in an["matches"][:6]:
            f = m["fwd"]
            ov.append(f'<tr><td>{m["date"]}</td>{num_cell(m["dist"], "{:.2f}")}' + "".join(pct_cell(f[k]) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr>")
        s = an["summary"]
        ov.append('<tr class="cur"><td>Median</td><td></td>' + "".join(pct_cell((s.get(k) or {}).get("median")) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr></table>"
                  '<p class="muted">Matches today against every day since 2000 on 8 features (S&P drawdown, VIX, credit spread, rates, dollar, gold, stock-bond correlation); nearby dates merged. Details on the Backtest tab.</p></div>')
    manual = D.get("manual") or {}
    if manual.get("capex"):
        ov.append('<h2>AI capex tracker (manual)</h2><div class="card"><ul class="alerts">' + "".join(
            f'<li><b>{esc(x.get("co", ""))}</b>: {esc(x.get("latest", ""))} <span class="muted">{esc(x.get("date", ""))}</span></li>' for x in manual["capex"]) + "</ul></div>")

    # ---------------- sections
    secs = {}
    for sk in C.SECTIONS:
        parts = []
        for gk in C.GROUP_NAMES:
            ids = [s["id"] for s in C.IND if s["sec"] == sk and s["grp"] == gk]
            if not ids:
                continue
            parts.append(f'<h2>{esc(C.GROUP_NAMES[gk])}</h2><div class="grid">' + "".join(ind_card(cards[i]) for i in ids if i in cards) + "</div>")
        secs[sk] = "".join(parts)

    # ---------------- AI funding chain extras (prepended to the AI tab)
    ai = D.get("ai")
    if ai:
        ic, lb = {"green": ("●", "Green"), "amber": ("▲", "Amber"), "red": ("■", "Red")}[ai["light"]]
        P = [f'<h2>AI funding chain: composite light</h2><div class="card s-{ai["light"]}"><div class="big"><span class="chip s-{ai["light"]}" style="font-size:16px"><span class="ic">{ic}</span>{lb}</span> {ai["n_bad"]}/3 pillars failing</div>'
             '<div class="pill">']
        for k, nm in (("credit", "Credit alarm"), ("monetize", "Monetization at the source"), ("capex", "Capex surprise")):
            r = ai["reasons"][k]
            P.append(f'<div>{chip("red" if r else "green")}</div><div><b>{nm}</b>: {esc("; ".join(r)) if r else "not triggered"}</div>')
        P.append('</div><p class="muted">One pillar failing = amber; two or more at once = red ("it only blows up when several negatives hit together"). Credit is the alarm, Anthropic&#39;s earnings are the verdict, and hyperscalers&#39; 2027 capex guidance decides whether to back upstream or the hyperscalers.</p></div>')
        P.append(f'<h2>Contagion chain: link {ai["stage"] or 0:.0f}/4</h2><div class="card"><div class="muted" style="margin-bottom:6px">20-day return of each link</div><div class="chain">')
        for i, l in enumerate(ai["chain"]):
            if i:
                P.append('<div class="ar">→</div>')
            r20 = "—" if l["r20"] is None else f'{l["r20"]:+.1f}%'
            r5 = "—" if l["r5"] is None else f'{l["r5"]:+.1f}%'
            P.append(f'<div class="lk{" hit" if l["hit"] else ""}"><b>{esc(l["name"]).replace("Neocloud", "Neo&shy;cloud").replace("Hyperscalers", "Hyper&shy;scalers")}</b>{r20}<div class="muted">5d {r5}</div><div class="muted">trigger {l["th"]:.0f}%</div></div>')
        P.append('</div><p class="muted">Checked from the weakest link to the strongest; a link only counts if every link before it has cracked. Spreading in order = contagion under way; hyperscalers falling while upstream holds is not this kind of contagion.</p></div>')
        secs["ai"] = "".join(P) + secs["ai"]
        Q = ['<h2>Layer B: credit signals updated from news</h2><div class="card tbl"><table><tr><th>Indicator</th><th>Value</th><th>As of</th><th>Light</th><th>Watch / Danger</th></tr>']
        for it in ai["b_layer"]:
            v = "—" if it.get("value") is None else f'{it["value"]:,}{esc(it["unit"])}'
            Q.append(f'<tr><td>{esc(it["name"])}<div class="muted">{esc(it.get("note", ""))}</div></td><td>{v}</td><td>{esc(it.get("date") or "—")}</td>'
                     f'<td>{chip(it["status"])}</td><td>{it["amber"]} / {it["red"]}</td></tr>')
        Q.append('</table><p class="muted">No free API; updated weekly from news. Treat anything older than two weeks as stale.</p></div>')
        Q.append('<h2>Layer C: quarterly earnings checklist</h2><div class="card"><ul class="alerts">')
        stl = {"pending": ("○", "Pending"), "ok": ("●", "Met"), "miss": ("■", "Missed")}
        for it in ai["checklist"]:
            icn, lbl = stl.get(it.get("status", "pending"), ("○", "Pending"))
            cls = {"ok": "green", "miss": "red"}.get(it.get("status"), "na")
            Q.append(f'<li><span class="chip s-{cls}"><span class="ic">{icn}</span>{lbl}</span> <b>{esc(it["co"])}</b>: {esc(it["item"])}</li>')
        Q.append('</ul></div><h2>Calendar</h2><div class="card"><ul class="alerts">')
        for ev in ai["calendar"]:
            when = "date TBD" if ev["days"] is None else ("today" if ev["days"] == 0 else f'in {ev["days"]} days' if ev["days"] > 0 else "yesterday")
            Q.append(f'<li><b>{esc(ev.get("date") or "TBD")}</b>{" (approx.)" if ev.get("approx") and ev.get("date") else ""} · {when}: {esc(ev["event"])}</li>')
        Q.append("</ul></div>")
        secs["ai"] += "".join(Q)

    # ---------------- backtest
    bt = D.get("bt") or {}
    B = []
    ep = bt.get("episodes") or {}
    cur = ep.get("current")
    if cur:
        N = cur["days"]
        B.append(f'<h2>This selloff vs past ones, at trading day {N}</h2><div class="card tbl"><table>'
                 '<tr><th>Episode</th><th>S&P</th><th>VIX high</th><th>Baa spread chg</th><th>Gold</th><th>Scen. A</th><th>B</th><th>C</th><th>D</th><th>Next 3M</th><th>Next 12M</th></tr>')
        sm = cur.get("scen_max") or {}
        B.append(f'<tr class="cur"><td>Current (from {cur["peak"].strftime("%Y-%m-%d")})</td>{pct_cell(cur["dd"])}{num_cell(cur.get("vix_max"))}{num_cell(cur.get("baa_chg"), "{:+.2f}")}{pct_cell(cur.get("gold_chg"))}'
                 + "".join(num_cell(sm.get(k), "{:.0f}") for k in "ABCD") + "<td>?</td><td>?</td></tr>")
        for e in ep["episodes"]:
            dn = e.get("dayN")
            if not dn:
                continue
            s2 = dn.get("scen_max") or {}
            af = e.get("afterN") or {}
            B.append(f'<tr><td>{esc(e["name"])} ({e["peak"].strftime("%Y-%m")})</td>{pct_cell(dn["dd"])}{num_cell(dn.get("vix_max"))}{num_cell(dn.get("baa_chg"), "{:+.2f}")}{pct_cell(dn.get("gold_chg"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + pct_cell(af.get("3M")) + pct_cell(af.get("12M")) + "</tr>")
        B.append('</table><p class="muted">Every episode is measured the same number of trading days from its S&P peak, so the comparison is like for like. "Next" is the S&P return from day N.</p></div>')
    if ep.get("episodes"):
        B.append('<h2>Past selloffs, peak to trough</h2><div class="card tbl"><table><tr><th>Episode</th><th>Max drawdown</th><th>Days to trough</th><th>Days to recover</th>'
                 '<th>VIX high</th><th>Baa chg</th><th>10Y chg</th><th>Dollar</th><th>Gold</th><th>TLT</th><th>TAIEX max DD</th><th>A</th><th>B</th><th>C</th><th>D</th></tr>')
        for e in ep["episodes"]:
            s2 = e.get("scen_max") or {}
            B.append(f'<tr><td>{esc(e["name"])} ({e["peak"].strftime("%Y-%m")})</td>{pct_cell(e["dd"])}{num_cell(e["to_trough"], "{:.0f}")}{num_cell(e["recover"], "{:.0f}")}'
                     f'{num_cell(e.get("vix_max"))}{num_cell(e.get("baa_chg"), "{:+.2f}")}{num_cell(e.get("y10_chg"), "{:+.2f}")}{pct_cell(e.get("usd_chg"))}{pct_cell(e.get("gold_chg"))}{pct_cell(e.get("tlt_chg"))}{pct_cell(e.get("twii_dd"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + "</tr>")
        B.append('</table><p class="muted">Days are trading days. Scenario columns are the highest score recomputed from the indicators available at the time; use them to sanity-check the scoring (e.g. D should be high in Mar 2020, C in 2008).</p></div>')
    rl = bt.get("rules") or []
    if rl:
        B.append('<h2>Conditional backtests: what happened next</h2><div class="card tbl"><table><tr><th>Condition</th><th>N</th><th>1M median</th><th>3M median</th><th>6M median</th><th>12M median</th><th>12M % up</th><th>Median max DD in 6M</th></tr>')
        for r in rl:
            g = lambda k, f="median": (r.get(k) or {}).get(f)  # noqa: E731
            nm = esc(r["name"]) + (' <span class="active">← active now</span>' if r.get("active") and not r.get("baseline") else "")
            B.append(f'<tr><td>{nm}<div class="muted">{esc(r.get("asset", ""))}</div></td><td>{r.get("n", 0)}</td>'
                     + pct_cell(g("1M")) + pct_cell(g("3M")) + pct_cell(g("6M")) + pct_cell(g("12M"))
                     + num_cell(g("12M", "pos"), "{:.0f}%") + pct_cell(g("maxDD6M")) + "</tr>")
        B.append('</table><p class="muted">Each episode counts once (1-month cooldown after a trigger). Treat results with N below 5 as anecdotal. Taiwan margin conditions fill in as margin history is backfilled on each run.</p>')
        B.append('<details><summary class="muted">Trigger dates for each condition</summary>' + "".join(
            f'<p class="muted"><b>{esc(r["name"])}</b>: {", ".join(r.get("dates") or []) or "—"}</p>' for r in rl if not r.get("baseline")) + "</details></div>")
    if an.get("matches"):
        labels = an["labels"]
        B.append('<h2>Historical analogs: feature comparison</h2><div class="card tbl"><table><tr><th>Date</th>' + "".join(f"<th>{esc(v)}</th>" for v in labels.values()) + "</tr>")
        B.append(f'<tr class="cur"><td>Today ({an["asof"]})</td>' + "".join(num_cell(an["today"][k], "{:+.2f}") for k in labels) + "</tr>")
        for m in an["matches"]:
            B.append(f'<tr><td>{m["date"]}</td>' + "".join(num_cell(m["feat"][k], "{:+.2f}") for k in labels) + "</tr>")
        B.append("</table></div>")
    B.append(f'<h2>Method and limitations</h2><div class="card muted">{D["method_html"]}</div>')
    B.append('<h2>Data status</h2><div class="card muted"><ul class="alerts">' + "".join(f"<li>{esc(x)}</li>" for x in D["log"]) + "</ul></div>")

    tabs = [("ov", "Overview", "".join(ov)), ("global", "Global", secs["global"]), ("us", "US", secs["us"]),
            ("ai", "AI funding chain", secs["ai"]), ("tw", "Taiwan", secs["tw"]), ("bt", "Backtest", "".join(B))]
    nav = "".join(f'<a href="#{t}" data-t="{t}" class="{"on" if i == 0 else ""}">{n}</a>' for i, (t, n, _) in enumerate(tabs))
    body = "".join(f'<section id="{t}" class="{"on" if i == 0 else ""}">{c}</section>' for i, (t, _, c) in enumerate(tabs))
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Market Stress Dashboard</title><style>{CSS}</style></head><body>'
            f'<header><h1>Market Stress Dashboard</h1><div class="sub">Updated {esc(D["updated"])} (Shanghai) · US data to {esc(D["asof_us"])} · Taiwan data to {esc(D["asof_tw"])}</div></header>'
            f'<nav>{nav}</nav>{body}<div id="tip"></div><script>{JS}</script>'
            f'<script type="application/json" id="data">{json.dumps({"scenarios": sc["now"], "updated": D["updated"]})}</script></body></html>')


METHOD_HTML = """
<p><b>Lights</b>: every indicator has a Watch and a Danger threshold. Fixed thresholds are anchored to past episodes (e.g. HY spread peaked near 5.3% in 2018Q4). Percentile-based indicators use their own history's 85th/97th percentile, computed only with data available at the time (no look-ahead).</p>
<p><b>Layer stress</b>: the average stress of the indicators in a layer. 0 = calm, 50 = right at the Watch line, 100 = everything past Danger.</p>
<p><b>Scenario scores</b>:
A Deleveraging correction = equity stress × (1 − 0.8×credit) × (1 − 0.8×funding): highest when equities panic but credit and funding are fine.
B Earnings-downgrade bear = weighted AI, AI contagion, policy and growth layers, plus a bump when capex cuts are announced.
C Credit event = mainly credit and AI credit, amplified by AI contagion and equity stress.
D Liquidity crisis = funding markets + cross-asset (stocks/bonds/gold falling together, dollar, yen).
Weights are judgment calls from our discussion, not statistically fitted; the Backtest tab shows the score each past episode would have produced, so you can check whether the scoring makes sense.</p>
<p><b>AI funding chain</b>: three pillars — credit alarm (BBB spread, credit-equity divergence, private credit, contagion stage ≥3, Layer B credit items), monetization (Anthropic and peers vs the checklist), and capex surprise. One failing = amber; two or more = red.</p>
<p><b>Data limits</b>: FRED only keeps about 3 years of the ICE HY/IG/BBB spreads, so long-history backtests use Moody's Baa − 10Y instead. Taiwan margin history is backfilled from the exchange a little on each run, so its backtests get more complete over time. The margin maintenance ratio is estimated as (margin shares × close) ÷ margin loans for listed stocks; it is not the same basis as brokers' account-level ratios, so read the direction more than the level.</p>
<p><b>Not investment advice.</b></p>
"""
