"""Static, mobile-first HTML dashboard (no external dependencies)."""
from __future__ import annotations

import html
import json
import math

from . import config as C

ST_LABEL = {"green": ("●", "正常"), "amber": ("▲", "警戒"), "red": ("■", "危險"), "na": ("○", "無資料"), "info": ("◆", "觀察")}

CSS = """
:root{--bg:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--line:#e6e5e0;
--series:#2a78d6;--good:#0ca30c;--warn:#fab219;--crit:#d03b3b;--chip:#f3f2ee}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--card:#232322;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#8f8e86;
--line:#383835;--series:#3987e5;--chip:#2d2d2b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif}
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
.chain .lk b{display:block;font-size:13px}.big{font-size:22px;font-weight:700}
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
        return '<div class="muted">歷史資料累積中</div>'
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
    chg_s = "" if chg is None else f"週變化 {'+' if chg >= 0 else '−'}{fmt(spec, abs(chg)).lstrip('+')}"
    pct = "" if c.get("pct") is None else f"歷史百分位 {c['pct']:.0f}%"
    th = c.get("th") or (None, None)
    ths = "" if th[0] is None or (isinstance(th[0], float) and math.isnan(th[0])) else \
        f"警戒 {fmt(spec, th[0])} / 危險 {fmt(spec, th[1])}"
    meta = " · ".join(x for x in (chg_s, pct, f"資料日 {c['asof']}" if c.get("asof") else "") if x)
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
    ov = ['<h2>情境判斷</h2><div class="scen">']
    for k, meta in C.SCENARIOS.items():
        v = sc["now"][k]
        d_prev = sc["delta_prev"].get(k)
        d5 = sc["delta_5d"].get(k)
        col = "var(--crit)" if v >= 60 else "var(--warn)" if v >= 35 else "var(--good)"
        dtxt = " · ".join(x for x in (f"較上次 {d_prev:+.0f}" if d_prev is not None else "",
                                       f"5日 {d5:+.0f}" if d5 is not None else "") if x)
        ov.append(f'<div class="card{" top1" if k == top else ""}"><div class="nm">{k}. {esc(meta["name"])}</div>'
                  f'<div class="an">類比：{esc(meta["analog"])}</div><div class="sc">{v:.0f}</div>'
                  f'<div class="bar"><i style="width:{v}%;background:{col}"></i></div>'
                  f'{sparkline(sc["hist"][k], sc["hist_d"], None)}<div class="muted">{esc(dtxt)}</div>'
                  f'<div class="ds">{esc(meta["desc"])}</div></div>')
    ov.append('</div><p class="legend">分數 0–100，由各層指標的壓力加權計算（公式見「回測」頁的方法說明）。它是壓力的相對強弱，不是機率。</p>')
    if D.get("ai"):
        ai0 = D["ai"]
        lb0 = {"green": "綠燈", "amber": "黃燈", "red": "紅燈"}[ai0["light"]]
        ov.append(f'<div class="card s-{ai0["light"]}" style="margin-top:8px"><b>AI 資金鏈：{chip(ai0["light"]).replace(ST_LABEL[ai0["light"]][1], lb0)}</b> '
                  f'{ai0["n_bad"]}/3 個支柱轉壞 · 傳導到第 {ai0["stage"] or 0:.0f}/4 環 <span class="muted">（詳見 AI 資金鏈頁）</span></div>')
    ov.append('<h2>各層壓力</h2><div class="card heat">')
    for gk, gv in D["groups"].items():
        if gv is None:
            continue
        col = "var(--crit)" if gv >= 70 else "var(--warn)" if gv >= 45 else "var(--good)"
        ov.append(f'<div class="n">{esc(C.GROUP_NAMES[gk])}</div><div class="bar" style="margin:0"><i style="width:{gv}%;background:{col}"></i></div><div class="v">{gv:.0f}</div>')
    ov.append("</div>")
    ov.append('<h2>變化與警報</h2><div class="card">')
    if D["transitions"]:
        ov.append('<h3 style="margin-top:0">較上次更新改變燈號</h3><ul class="alerts">' + "".join(
            f'<li>{chip(t["to"])} {esc(C.IND_BY_ID[t["id"]]["name"])}：{fmt(C.IND_BY_ID[t["id"]], t["value"])}（原為{ST_LABEL[t["from"]][1]}）</li>'
            for t in D["transitions"]) + "</ul>")
    reds = [c for c in D["cards"] if c["status"] == "red"]
    ov.append('<h3>目前危險</h3>' + ('<ul class="alerts">' + "".join(
        f'<li>{esc(C.IND_BY_ID[c["id"]]["name"])}：<b>{fmt(C.IND_BY_ID[c["id"]], c["value"])}</b> {esc(C.IND_BY_ID[c["id"]]["unit"])}</li>' for c in reds)
        + "</ul>" if reds else '<div class="muted">無</div>'))
    ov.append("</div>")
    an = (D.get("bt") or {}).get("analogs") or {}
    if an.get("matches"):
        ov.append('<h2>歷史上最相似的日子</h2><div class="card tbl"><table><tr><th>日期</th><th>相似度距離</th><th>之後 1M</th><th>3M</th><th>6M</th><th>12M</th><th>6M 內最大跌幅</th></tr>')
        for m in an["matches"][:6]:
            f = m["fwd"]
            ov.append(f'<tr><td>{m["date"]}</td>{num_cell(m["dist"], "{:.2f}")}' + "".join(pct_cell(f[k]) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr>")
        s = an["summary"]
        ov.append('<tr class="cur"><td>中位數</td><td></td>' + "".join(pct_cell((s.get(k) or {}).get("median")) for k in ("1M", "3M", "6M", "12M", "maxDD6M")) + "</tr></table>"
                  '<p class="muted">用 S&P 回撤、VIX、信用利差、利率、美元、黃金、股債相關性 8 個特徵，在 2000 年以來的每一天裡找出與今天最接近的日子（相鄰日期合併）。詳見回測頁。</p></div>')
    manual = D.get("manual") or {}
    if manual.get("capex"):
        ov.append('<h2>AI 資本支出追蹤（手動）</h2><div class="card"><ul class="alerts">' + "".join(
            f'<li><b>{esc(x.get("co", ""))}</b>：{esc(x.get("latest", ""))} <span class="muted">{esc(x.get("date", ""))}</span></li>' for x in manual["capex"]) + "</ul></div>")

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
        ic, lb = {"green": ("●", "綠燈"), "amber": ("▲", "黃燈"), "red": ("■", "紅燈")}[ai["light"]]
        P = [f'<h2>AI 資金鏈綜合燈號</h2><div class="card s-{ai["light"]}"><div class="big"><span class="chip s-{ai["light"]}" style="font-size:16px"><span class="ic">{ic}</span>{lb}</span> {ai["n_bad"]}/3 個支柱轉壞</div>'
             '<div class="pill">']
        for k, nm in (("credit", "信用警報"), ("monetize", "源頭變現"), ("capex", "capex 意外")):
            r = ai["reasons"][k]
            P.append(f'<div>{chip("red" if r else "green")}</div><div><b>{nm}</b>：{esc("、".join(r)) if r else "未觸發"}</div>')
        P.append('</div><p class="muted">只有一個支柱轉壞 = 黃燈；兩個以上同時發生 = 紅燈（「多個利空同時發生才會引爆」）。信用指標是警報器，Anthropic 財報是判決，巨頭 2027 capex 指引決定該押上游還是押巨頭。</p></div>')
        P.append(f'<h2>風險傳導鏈：第 {ai["stage"] or 0:.0f}/4 環</h2><div class="card"><div class="muted" style="margin-bottom:6px">各環節 20 日報酬</div><div class="chain">')
        for i, l in enumerate(ai["chain"]):
            if i:
                P.append('<div class="ar">→</div>')
            r20 = "—" if l["r20"] is None else f'{l["r20"]:+.1f}%'
            r5 = "—" if l["r5"] is None else f'{l["r5"]:+.1f}%'
            P.append(f'<div class="lk{" hit" if l["hit"] else ""}"><b>{esc(l["name"])}</b>{r20}<div class="muted">5日 {r5}</div><div class="muted">門檻 {l["th"]:.0f}%</div></div>')
        P.append('</div><p class="muted">由最弱的環節往最強的依序檢查：前面的環節都跌破門檻，才往下一環計算。依序擴散 = 傳導中；只有巨頭跌、上游沒跌，就不是這種傳導。</p></div>')
        secs["ai"] = "".join(P) + secs["ai"]
        Q = ['<h2>B 層：手動 / 新聞更新的信用指標</h2><div class="card tbl"><table><tr><th>指標</th><th>數值</th><th>資料日</th><th>燈號</th><th>門檻</th></tr>']
        for it in ai["b_layer"]:
            v = "—" if it.get("value") is None else f'{it["value"]:,}{esc(it["unit"])}'
            Q.append(f'<tr><td>{esc(it["name"])}<div class="muted">{esc(it.get("note", ""))}</div></td><td>{v}</td><td>{esc(it.get("date") or "—")}</td>'
                     f'<td>{chip(it["status"])}</td><td>{it["amber"]} / {it["red"]}</td></tr>')
        Q.append('</table><p class="muted">沒有免費 API，每週從新聞更新。資料日超過兩週的請當成過期資料。</p></div>')
        Q.append('<h2>C 層：每季財報檢查清單</h2><div class="card"><ul class="alerts">')
        stl = {"pending": ("○", "待確認"), "ok": ("●", "達標"), "miss": ("■", "未達標")}
        for it in ai["checklist"]:
            icn, lbl = stl.get(it.get("status", "pending"), ("○", "待確認"))
            cls = {"ok": "green", "miss": "red"}.get(it.get("status"), "na")
            Q.append(f'<li><span class="chip s-{cls}"><span class="ic">{icn}</span>{lbl}</span> <b>{esc(it["co"])}</b>：{esc(it["item"])}</li>')
        Q.append('</ul></div><h2>行事曆</h2><div class="card"><ul class="alerts">')
        for ev in ai["calendar"]:
            when = "時間待定" if ev["days"] is None else ("今天" if ev["days"] == 0 else f'{ev["days"]} 天後' if ev["days"] > 0 else "昨天")
            Q.append(f'<li><b>{esc(ev.get("date") or "待定")}</b>{"（約）" if ev.get("approx") and ev.get("date") else ""} · {when}：{esc(ev["event"])}</li>')
        Q.append("</ul></div>")
        secs["ai"] += "".join(Q)

    # ---------------- backtest
    bt = D.get("bt") or {}
    B = []
    ep = bt.get("episodes") or {}
    cur = ep.get("current")
    if cur:
        N = cur["days"]
        B.append(f'<h2>本輪 vs 歷次回檔：在第 {N} 個交易日時</h2><div class="card tbl"><table>'
                 '<tr><th>事件</th><th>S&P</th><th>VIX 高</th><th>Baa 利差變化</th><th>黃金</th><th>情境A</th><th>B</th><th>C</th><th>D</th><th>之後 3M</th><th>之後 12M</th></tr>')
        sm = cur.get("scen_max") or {}
        B.append(f'<tr class="cur"><td>本輪 ({cur["peak"].strftime("%Y-%m-%d")} 起)</td>{pct_cell(cur["dd"])}{num_cell(cur.get("vix_max"))}{num_cell(cur.get("baa_chg"), "{:+.2f}")}{pct_cell(cur.get("gold_chg"))}'
                 + "".join(num_cell(sm.get(k), "{:.0f}") for k in "ABCD") + "<td>?</td><td>?</td></tr>")
        for e in ep["episodes"]:
            dn = e.get("dayN")
            if not dn:
                continue
            s2 = dn.get("scen_max") or {}
            af = e.get("afterN") or {}
            B.append(f'<tr><td>{esc(e["name"])} ({e["peak"].strftime("%Y-%m")})</td>{pct_cell(dn["dd"])}{num_cell(dn.get("vix_max"))}{num_cell(dn.get("baa_chg"), "{:+.2f}")}{pct_cell(dn.get("gold_chg"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + pct_cell(af.get("3M")) + pct_cell(af.get("12M")) + "</tr>")
        B.append('</table><p class="muted">每個事件都從 S&P 高點起算相同的交易日數，讓比較基準一致。「之後」是從第 N 天起算的 S&P 報酬。</p></div>')
    if ep.get("episodes"):
        B.append('<h2>歷次回檔全貌（高點 → 低點）</h2><div class="card tbl"><table><tr><th>事件</th><th>最大跌幅</th><th>到底天數</th><th>收復天數</th>'
                 '<th>VIX 高</th><th>Baa 變化</th><th>10Y 變化</th><th>美元</th><th>黃金</th><th>TLT</th><th>加權最大回撤</th><th>A</th><th>B</th><th>C</th><th>D</th></tr>')
        for e in ep["episodes"]:
            s2 = e.get("scen_max") or {}
            B.append(f'<tr><td>{esc(e["name"])} ({e["peak"].strftime("%Y-%m")})</td>{pct_cell(e["dd"])}{num_cell(e["to_trough"], "{:.0f}")}{num_cell(e["recover"], "{:.0f}")}'
                     f'{num_cell(e.get("vix_max"))}{num_cell(e.get("baa_chg"), "{:+.2f}")}{num_cell(e.get("y10_chg"), "{:+.2f}")}{pct_cell(e.get("usd_chg"))}{pct_cell(e.get("gold_chg"))}{pct_cell(e.get("tlt_chg"))}{pct_cell(e.get("twii_dd"))}'
                     + "".join(num_cell(s2.get(k), "{:.0f}") for k in "ABCD") + "</tr>")
        B.append('</table><p class="muted">天數為交易日。情境分數是用當時可得的指標回推計算的最高值，可以拿來檢驗評分方式：例如 2020/3 的 D 分數、2008 的 C 分數應該偏高。</p></div>')
    rl = bt.get("rules") or []
    if rl:
        B.append('<h2>條件回測：出現這種狀況之後怎麼走</h2><div class="card tbl"><table><tr><th>條件</th><th>次數</th><th>1M 中位</th><th>3M 中位</th><th>6M 中位</th><th>12M 中位</th><th>12M 上漲機率</th><th>6M 內最大跌幅中位</th></tr>')
        for r in rl:
            g = lambda k, f="median": (r.get(k) or {}).get(f)  # noqa: E731
            nm = esc(r["name"]) + (' <span class="active">← 現在成立</span>' if r.get("active") and not r.get("baseline") else "")
            B.append(f'<tr><td>{nm}<div class="muted">{esc(r.get("asset", ""))}</div></td><td>{r.get("n", 0)}</td>'
                     + pct_cell(g("1M")) + pct_cell(g("3M")) + pct_cell(g("6M")) + pct_cell(g("12M"))
                     + num_cell(g("12M", "pos"), "{:.0f}%") + pct_cell(g("maxDD6M")) + "</tr>")
        B.append('</table><p class="muted">同一波行情只計一次（觸發後冷卻 1 個月）。次數少於 5 的結果只能當參考。台股的融資條件需要等融資歷史補齊（每次更新都會往前補）。</p>')
        B.append('<details><summary class="muted">每個條件的觸發日期</summary>' + "".join(
            f'<p class="muted"><b>{esc(r["name"])}</b>：{", ".join(r.get("dates") or []) or "—"}</p>' for r in rl if not r.get("baseline")) + "</details></div>")
    if an.get("matches"):
        labels = an["labels"]
        B.append('<h2>歷史類比：特徵比較</h2><div class="card tbl"><table><tr><th>日期</th>' + "".join(f"<th>{esc(v)}</th>" for v in labels.values()) + "</tr>")
        B.append(f'<tr class="cur"><td>今天 ({an["asof"]})</td>' + "".join(num_cell(an["today"][k], "{:+.2f}") for k in labels) + "</tr>")
        for m in an["matches"]:
            B.append(f'<tr><td>{m["date"]}</td>' + "".join(num_cell(m["feat"][k], "{:+.2f}") for k in labels) + "</tr>")
        B.append("</table></div>")
    B.append(f'<h2>方法與限制</h2><div class="card muted">{D["method_html"]}</div>')
    B.append('<h2>數據狀態</h2><div class="card muted"><ul class="alerts">' + "".join(f"<li>{esc(x)}</li>" for x in D["log"]) + "</ul></div>")

    tabs = [("ov", "總覽", "".join(ov)), ("global", "全球", secs["global"]), ("us", "美國", secs["us"]),
            ("ai", "AI 資金鏈", secs["ai"]), ("tw", "台股", secs["tw"]), ("bt", "回測", "".join(B))]
    nav = "".join(f'<a href="#{t}" data-t="{t}" class="{"on" if i == 0 else ""}">{n}</a>' for i, (t, n, _) in enumerate(tabs))
    body = "".join(f'<section id="{t}" class="{"on" if i == 0 else ""}">{c}</section>' for i, (t, _, c) in enumerate(tabs))
    return (f'<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>市場壓力儀表板</title><style>{CSS}</style></head><body>'
            f'<header><h1>市場壓力儀表板</h1><div class="sub">更新：{esc(D["updated"])}（上海時間）· 美股資料至 {esc(D["asof_us"])} · 台股資料至 {esc(D["asof_tw"])}</div></header>'
            f'<nav>{nav}</nav>{body}<div id="tip"></div><script>{JS}</script>'
            f'<script type="application/json" id="data">{json.dumps({"scenarios": sc["now"], "updated": D["updated"]})}</script></body></html>')


METHOD_HTML = """
<p><b>燈號</b>：每個指標都有「警戒」與「危險」門檻。固定門檻參考過去事件的水準（例如 HY 利差 2018Q4 高點約 5.3%）；標示為百分位的指標，則用該指標自有歷史的 85%/97% 分位（往回算，不偷看未來）。</p>
<p><b>各層壓力</b>：同一層指標的壓力平均。0 = 平靜，50 = 剛好在警戒線，100 = 全部超過危險線。</p>
<p><b>情境分數</b>：
A 去槓桿修正 = 股市壓力 ×（1 − 0.8×信用）×（1 − 0.8×資金）：股市恐慌但信用和資金市場沒事時最高。
B 盈利下修熊市 = AI 層、政策層、增長層加權，capex 被削減時再加分。
C 信用事件 = 以信用層為主，AI 層和股市層的壓力會放大。
D 流動性危機 = 資金市場層 + 跨資產層（股債金同跌、美元、日圓）。
權重是根據我們的討論設定的經驗值，不是用統計擬合出來的；回測頁列出每個歷史事件回推的分數，可以直接檢查這套評分是否合理。</p>
<p><b>資料限制</b>：FRED 上的 ICE HY/IG 利差只保留最近約 3 年，所以長歷史的回測改用 Moody's Baa−10Y 利差。台股融資歷史是從證交所逐日補抓，每次更新往前補一段，回測會隨之變完整。融資維持率是用「上市個股融資餘額×收盤價 ÷ 融資金額」估算，與券商公布的整戶維持率口徑不同，看方向比看絕對值可靠。</p>
<p><b>這不是投資建議。</b></p>
"""
