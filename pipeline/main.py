"""Entry point: fetch -> indicators -> backtest -> dashboard -> Telegram."""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from . import backtest, config as C, fetch, indicators as I, render, telegram

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
DOCS = ROOT / "docs"
WEEKLY = {"stlfsi", "nfci", "claims"}


def _f(x):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else float(x)


def load_raw(do_fetch: bool, twse_budget: int):
    if do_fetch:
        fred = fetch.fetch_fred()
        yahoo = fetch.fetch_yahoo()
        # TWSE trading days: TAIEX dates when available, otherwise all weekdays
        # (holidays just return empty and are skipped after two tries)
        if "TWII" in yahoo and yahoo["TWII"].notna().sum() > 1000:
            tw = yahoo["TWII"].dropna()
            tw_days = [d.date() for d in tw.index[tw.index >= "2015-01-01"]]
        else:
            tw_days = [d.date() for d in pd.bdate_range("2015-01-01", pd.Timestamp.today())]
        twse = fetch.fetch_twse(tw_days, budget_s=twse_budget)
    else:
        rd = lambda n: pd.read_csv(fetch.RAW / n, index_col=0, parse_dates=True) if (fetch.RAW / n).exists() else pd.DataFrame()  # noqa: E731
        fred, yahoo, twse = rd("fred.csv"), rd("yahoo.csv"), rd("twse.csv")
        fetch.log("[cache] using cached data, no fetch")
    return fred, yahoo, twse


def ai_module(raw, cards, manual, today):
    """AI funding-chain composite: three pillars (credit alarm / monetization /
    capex surprise). Red when two or more fail at once."""
    cmap = {c["id"]: c for c in cards}
    flags = manual.get("flags", {})
    b = []
    for it in manual.get("b_layer", []):
        v = it.get("value")
        stv = I.stress_value({"dir": it["dir"]}, float(v), it["amber"], it["red"]) if v is not None else float("nan")
        b.append(dict(it, status=I.status_of(stv)))
    reasons = {"credit": [], "monetize": [], "capex": []}
    for i in ("bbb_oas", "credit_eq_div", "bizd_hyg_1m", "owl_dd"):
        if cmap.get(i, {}).get("status") == "red":
            reasons["credit"].append(C.IND_BY_ID[i]["name"])
    stage = cmap.get("ai_chain_stage", {}).get("value")
    if stage is not None and stage >= 3:
        reasons["credit"].append(f"contagion reached link {stage:.0f}")
    for it in b:
        if it["status"] == "red":
            reasons[it.get("pillar", "credit")].append(it["name"])
    for it in manual.get("checklist", []):
        if it.get("status") == "miss":
            reasons[it.get("pillar", "credit")].append(f'{it["co"]}: {it["item"][:40]}…')
    if flags.get("monetization_miss"):
        reasons["monetize"].append("monetization miss (flagged)")
    if flags.get("capex_surprise") or manual.get("capex_cut_announced"):
        reasons["capex"].append("capex surprise (flagged)")
    n_bad = sum(1 for v in reasons.values() if v)
    light = "red" if n_bad >= 2 else "amber" if n_bad == 1 else "green"
    cal = []
    for ev in manual.get("calendar", []):
        d = ev.get("date")
        days = (pd.Timestamp(d) - pd.Timestamp(today.date())).days if d else None
        if days is None or days >= -1:
            cal.append(dict(ev, days=days))
    cal.sort(key=lambda e: (e["days"] is None, e["days"] if e["days"] is not None else 0))
    return dict(light=light, n_bad=n_bad, reasons=reasons, stage=stage,
                chain=I.chain_detail(raw), b_layer=b, checklist=manual.get("checklist", []), calendar=cal)


def build(raw, ind, st, th, gs, scen, manual, prev):
    cards, stale = [], []
    today = raw.index[-1]
    for spec in C.IND:
        i = spec["id"]
        s = ind[i].dropna()
        if s.empty:
            cards.append(dict(id=i, value=None, status="na", spark=[], spark_d=[], th=th.get(i), asof=None))
            continue
        if spec["mode"] == "info":
            d = s.index[-1]
            win = ind[i].loc[today - pd.Timedelta(days=380):]
            prev5 = s.loc[: d - pd.Timedelta(days=7)]
            cards.append(dict(id=i, value=float(s.iloc[-1]), status="info",
                              chg_1w=_f(float(s.iloc[-1]) - float(prev5.iloc[-1])) if len(prev5) else None,
                              pct=float((s < s.iloc[-1]).mean() * 100) if len(s) > 250 else None, th=(None, None),
                              spark=[_f(v) for v in win.values], spark_d=[t.strftime("%y/%m/%d") for t in win.index],
                              asof=d.strftime("%m/%d")))
            continue
        d = s.index[-1]
        x = float(s.iloc[-1])
        stv = st[i].loc[:d].dropna()
        status = I.status_of(float(stv.iloc[-1])) if len(stv) else "na"
        if status == "na" and spec["mode"] == "pct":
            status = "hist"
        age = (today - d).days
        if age > (14 if i in WEEKLY else 7):
            stale.append(spec["name"])
        prev5 = s.loc[: d - pd.Timedelta(days=7)]
        chg = x - float(prev5.iloc[-1]) if len(prev5) else None
        pct = float((s < x).mean() * 100) if len(s) > 250 else None
        win = ind[i].loc[today - pd.Timedelta(days=380):]
        cards.append(dict(id=i, value=x, status=status, chg_1w=_f(chg), pct=pct,
                          th=tuple(_f(t) for t in th.get(i, (None, None))),
                          spark=[_f(v) for v in win.values], spark_d=[t.strftime("%y/%m/%d") for t in win.index],
                          asof=d.strftime("%m/%d")))
    prev_st = (prev or {}).get("status", {})
    transitions = [dict(id=c["id"], frm=prev_st[c["id"]], to=c["status"], value=c["value"])
                   for c in cards if c["id"] in prev_st and prev_st[c["id"]] != c["status"]
                   and c["status"] not in ("na", "hist") and prev_st[c["id"]] not in ("na", "hist")]
    for t in transitions:
        t["from"] = t.pop("frm")
    order = {"red": 0, "amber": 1, "green": 2}
    transitions.sort(key=lambda t: order.get(t["to"], 3))

    sc_now = {k: float(scen[k].iloc[-1]) for k in "ABCD"}
    prev_sc = (prev or {}).get("scenarios", {})
    hist = scen.iloc[-130:]
    s5 = scen.iloc[-6] if len(scen) > 6 else None
    scen_d = dict(now=sc_now,
                  delta_prev={k: sc_now[k] - prev_sc[k] for k in "ABCD" if k in prev_sc},
                  delta_5d={k: sc_now[k] - float(s5[k]) for k in "ABCD"} if s5 is not None else {},
                  hist={k: [_f(v) for v in hist[k].values] for k in "ABCD"},
                  hist_d=[t.strftime("%y/%m/%d") for t in hist.index])
    groups = {g: (_f(gs[g].iloc[-1] * 100) if g in gs else None) for g in C.GROUP_NAMES}

    prices = {}
    for k in ["SPX", "NDX", "SOX", "GOLD", "BTC", "N225", "KOSPI", "HSI", "TWII", "TWOII", "TSMC"]:
        if k in raw:
            s = backtest._native(raw[k])
            if len(s) > 2:
                prices[k] = dict(level=float(s.iloc[-1]), chg1d=float((s.iloc[-1] / s.iloc[-2] - 1) * 100),
                                 date=s.index[-1].strftime("%m/%d"))
    asof = lambda cols: max((raw[c].dropna().index.max() for c in cols if c in raw and raw[c].notna().any()), default=None)  # noqa: E731
    a_us, a_tw = asof(["SPX", "VIX"]), asof(["TWII"])
    return dict(cards=cards, transitions=transitions, scenarios=scen_d, groups=groups, prices=prices,
                manual=manual, stale=stale,
                asof_us=a_us.strftime("%Y-%m-%d") if a_us is not None else "—",
                asof_tw=a_tw.strftime("%Y-%m-%d") if a_tw is not None else "—")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", default="auto", choices=["auto", "morning", "evening"])
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--twse-budget", type=int, default=int(os.environ.get("TWSE_BUDGET", "420")))
    a = ap.parse_args()

    now = datetime.now(ZoneInfo(C.TZ))
    slot = a.slot if a.slot != "auto" else ("morning" if now.hour < 12 else "evening")
    fred, yahoo, twse = load_raw(not a.no_fetch, a.twse_budget)
    raw = I.daily_frame(fred, yahoo, twse)
    ind = I.compute(raw)
    st, th = I.stress_frame(ind)
    gs = I.group_scores(st)
    manual_p = STATE / "manual.json"
    manual = json.loads(manual_p.read_text()) if manual_p.exists() else {}
    scen = I.scenario_scores(gs, manual)
    prev_p = STATE / "last.json"
    prev = json.loads(prev_p.read_text()) if prev_p.exists() else None

    D = build(raw, ind, st, th, gs, scen, manual, prev)
    D["ai"] = ai_module(raw, D["cards"], manual, now)
    D["bt"] = backtest.run_all(raw, ind, scen)
    D["updated"] = now.strftime("%Y-%m-%d %H:%M")
    D["log"] = fetch.LOG
    D["method_html"] = render.METHOD_HTML

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(render.render(D), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("")
    summary = dict(updated=D["updated"], slot=slot, scenarios=D["scenarios"]["now"], groups=D["groups"],
                   indicators={c["id"]: dict(value=c["value"], status=c["status"], asof=c.get("asof")) for c in D["cards"]},
                   prices=D["prices"], ai=dict(light=D["ai"]["light"], reasons=D["ai"]["reasons"], stage=D["ai"]["stage"]),
                   active_rules=[r["name"] for r in (D["bt"].get("rules") or []) if r.get("active") and not r.get("baseline")],
                   analogs=(D["bt"].get("analogs") or {}).get("matches", [])[:5])
    (DOCS / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"[render] docs/index.html done; scenarios {D['scenarios']['now']}")

    repo = os.environ.get("GITHUB_REPOSITORY")
    url = os.environ.get("DASHBOARD_URL") or (f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/" if repo else None)
    if not a.no_notify:
        try:
            telegram.send(telegram.build_message(D, slot, url))
        except Exception as e:  # noqa: BLE001
            print(f"[Telegram] send failed: {e}")
    else:
        print(telegram.build_message(D, slot, url))

    STATE.mkdir(exist_ok=True)
    prev_p.write_text(json.dumps(dict(updated=D["updated"], scenarios=D["scenarios"]["now"],
                                      status={c["id"]: c["status"] for c in D["cards"]},
                                      ai_light=D["ai"]["light"]), ensure_ascii=False))
    hp = STATE / "runs.csv"
    row = pd.DataFrame([{"time": D["updated"], "slot": slot, **D["scenarios"]["now"]}])
    row.to_csv(hp, mode="a", header=not hp.exists(), index=False)


if __name__ == "__main__":
    main()
