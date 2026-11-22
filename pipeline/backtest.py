"""Backtests on real history: past episodes, conditional forward returns,
nearest-neighbour historical analogs, and the Taiwan margin rule."""
from __future__ import annotations

import numpy as np
import pandas as pd

EPISODES = [
    ("1998-07-17", "LTCM / Asian crisis"),
    ("2000-03-24", "Dot-com bust"),
    ("2007-10-09", "Global financial crisis"),
    ("2010-04-23", "Euro debt / flash crash"),
    ("2011-04-29", "US downgrade"),
    ("2015-07-20", "Yuan devaluation"),
    ("2018-01-26", "Volmageddon"),
    ("2018-09-20", "2018Q4 hikes + QT"),
    ("2020-02-19", "Covid liquidity crisis"),
    ("2022-01-03", "2022 rate-hike bear"),
    ("2023-07-31", "2023 rate shock"),
    ("2024-07-16", "Yen carry unwind"),
    ("2025-02-19", "2025 tariffs"),
]
HORIZONS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}


def _native(s: pd.Series) -> pd.Series:
    s = s.dropna()
    return s[s.diff().fillna(1) != 0]


def fwd_returns(px: pd.Series, dates) -> pd.DataFrame:
    px = _native(px)
    rows = []
    for d in dates:
        i = px.index.searchsorted(d)
        if i >= len(px):
            continue
        row = {"date": px.index[i]}
        for k, h in HORIZONS.items():
            row[k] = (px.iloc[i + h] / px.iloc[i] - 1) * 100 if i + h < len(px) else np.nan
        w = px.iloc[i:i + 127]
        row["maxDD6M"] = (w.min() / px.iloc[i] - 1) * 100 if len(w) > 5 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _events(cond: pd.Series, cooldown=21) -> list:
    cond = cond.fillna(False).astype(bool)
    out, last = [], None
    for d, v in cond.items():
        if v and (last is None or (d - last).days > cooldown * 1.45):
            out.append(d)
        if v:
            last = d
    return out


def _summ(fr: pd.DataFrame) -> dict:
    res = {"n": int(len(fr))}
    for k in list(HORIZONS) + ["maxDD6M"]:
        v = fr[k].dropna() if k in fr else pd.Series(dtype=float)
        res[k] = {"median": float(v.median()) if len(v) else None,
                  "pos": float((v > 0).mean() * 100) if len(v) else None,
                  "min": float(v.min()) if len(v) else None,
                  "n": int(len(v))}
    return res


# ---------------------------------------------------------------- episodes
def episodes(raw, ind, scen) -> dict:
    spx = _native(raw["SPX"])
    eps = []
    cur = None
    last = spx.iloc[-252:]
    peak_d = last.idxmax()
    cur_dd = (spx.iloc[-1] / last.max() - 1) * 100
    days_in = int((spx.index > peak_d).sum())
    if cur_dd < -5:
        cur = dict(peak=peak_d, name="Current (ongoing)", days=days_in, dd=cur_dd)

    def snap(t0, t1):
        w = slice(t0, t1)
        ib = lambda c: ind[c].loc[w] if c in ind else pd.Series(dtype=float)  # noqa: E731
        rb = lambda c: raw[c].loc[w].dropna() if c in raw else pd.Series(dtype=float)  # noqa: E731
        ch = lambda s: float(s.iloc[-1] - s.iloc[0]) if len(s) > 1 else None  # noqa: E731
        pc = lambda s: float((s.iloc[-1] / s.iloc[0] - 1) * 100) if len(s) > 1 else None  # noqa: E731
        mx = lambda s: float(s.max()) if len(s.dropna()) else None  # noqa: E731
        sc = scen.loc[w] if len(scen.loc[w]) else None
        return {
            "vix_max": mx(ib("vix")),
            "baa_chg": ch(rb("BAA10Y")),
            "hy_max": mx(ib("hy_oas")),
            "move_max": mx(ib("move")),
            "y10_chg": ch(rb("DGS10")),
            "usd_chg": pc(rb("DXY")),
            "gold_chg": pc(rb("GOLD")),
            "tlt_chg": pc(rb("TLT")),
            "twii_dd": float(ib("twii_dd").min()) if len(ib("twii_dd").dropna()) else None,
            "scen_max": {k: float(sc[k].max()) for k in "ABCD"} if sc is not None else None,
        }

    for d0, name in EPISODES:
        d0 = pd.Timestamp(d0)
        if d0 < spx.index[0]:
            continue
        win = spx.loc[d0 - pd.Timedelta(days=21): d0 + pd.Timedelta(days=21)]
        p = win.idxmax()
        pv = spx.loc[p]
        after = spx.loc[p:]
        rec = after[after.index > p]
        rec = rec[rec >= pv]
        rec_d = rec.index[0] if len(rec) else None
        seg = spx.loc[p: rec_d] if rec_d is not None else after.iloc[:1000]
        tr = seg.idxmin()
        e = dict(peak=p, name=name, dd=float((seg.min() / pv - 1) * 100),
                 to_trough=int(((spx.index > p) & (spx.index <= tr)).sum()),
                 recover=int(((spx.index > p) & (spx.index <= rec_d)).sum()) if rec_d is not None else None)
        e.update(snap(p, tr))
        if cur:  # same-day-count comparison with the current episode
            j = spx.index.searchsorted(p) + cur["days"]
            if j < len(spx):
                dN = spx.index[j]
                e["dayN"] = dict(dd=float((spx.loc[p:dN].iloc[-1] / pv - 1) * 100),
                                 **{k: v for k, v in snap(p, dN).items() if k in ("vix_max", "baa_chg", "hy_max", "y10_chg", "gold_chg", "scen_max")})
                # what happened after day N
                fr = fwd_returns(raw["SPX"], [dN])
                e["afterN"] = fr.iloc[0].drop("date").to_dict() if len(fr) else None
        eps.append(e)
    if cur:
        cur.update(snap(cur["peak"], spx.index[-1]))
    return {"episodes": eps, "current": cur}


# ---------------------------------------------------------------- rules
def rules(raw, ind) -> list[dict]:
    spx = raw["SPX"]
    baa3m = raw["BAA10Y"] - raw["BAA10Y"].shift(63)
    dff6m = raw["DFF"] - raw["DFF"].shift(126)
    spy5 = raw["SPY"].pct_change(5, fill_method=None) * 100
    tlt5 = raw["TLT"].pct_change(5, fill_method=None) * 100
    gold5 = raw["GOLD"].pct_change(5, fill_method=None) * 100
    spx5 = spx.pct_change(5, fill_method=None) * 100
    R = [
        ("VIX ≥ 35, credit calm (Baa spread 3M widening < 0.5)", (ind["vix"] >= 35) & (baa3m < 0.5), "SPX"),
        ("VIX ≥ 35, credit worsening (Baa spread 3M widening ≥ 0.5)", (ind["vix"] >= 35) & (baa3m >= 0.5), "SPX"),
        ("S&P down ≥ 10%, Fed hiking (6M +25bp or more)", (ind["spx_dd"] <= -10) & (dff6m > 0.25), "SPX"),
        ("S&P down ≥ 10%, Fed cutting (6M −25bp or more)", (ind["spx_dd"] <= -10) & (dff6m < -0.25), "SPX"),
        ("S&P down ≥ 10%, Fed on hold", (ind["spx_dd"] <= -10) & (dff6m.abs() <= 0.25), "SPX"),
        ("Stocks and bonds down for a week (SPY 5d < −3% and TLT < −1%)", (spy5 < -3) & (tlt5 < -1), "SPX"),
        ("Stocks and gold down for a week (both 5d < −4%)", (spx5 < -4) & (gold5 < -4), "SPX"),
        ("VIX curve inverted (VIX/VIX3M > 1.05)", ind["vix_term"] > 1.05, "SPX"),
        ("All S&P days (baseline)", spx.notna(), "SPX"),
        ("TAIEX down ≥ 20%", ind["twii_dd"] <= -20, "TWII"),
        ("TAIEX down ≥ 20%, margin cut ≥ index fall", (ind["twii_dd"] <= -20) & (ind["tw_delever"] >= 1), "TWII"),
        ("TAIEX down ≥ 20%, margin cut < index fall", (ind["twii_dd"] <= -20) & (ind["tw_delever"] < 1), "TWII"),
        ("TAIEX down ≥ 15%, ≥ 100 stocks limit-down", (ind["twii_dd"] <= -15) & (ind["tw_limitdown"] >= 100), "TWII"),
    ]
    out = []
    for name, cond, px in R:
        baseline = name.startswith("All S&P")
        ev = list(cond[cond.fillna(False)].index[::21]) if baseline else _events(cond)
        fr = fwd_returns(raw[px], ev) if px in raw else pd.DataFrame()
        s = _summ(fr) if len(fr) else {"n": 0}
        s.update(name=name, asset="S&P 500" if px == "SPX" else "TAIEX",
                 active=bool(cond.fillna(False).iloc[-5:].any()),
                 dates=[d.strftime("%Y-%m-%d") for d in (fr["date"] if len(fr) else [])][-12:] if not baseline else [],
                 baseline=baseline)
        out.append(s)
    return out


# ---------------------------------------------------------------- analogs
def analogs(raw, ind, k=8) -> dict:
    spx = raw["SPX"]
    y10 = raw["DGS10"]
    feats = pd.DataFrame({
        "spx_dd": ind["spx_dd"],
        "spx_1m": spx.pct_change(21, fill_method=None) * 100,
        "vix": ind["vix"],
        "baa_3m": raw["BAA10Y"] - raw["BAA10Y"].shift(63),
        "y10_3m": (y10 - y10.shift(63)) * 100,
        "usd_1m": raw["DXY"].pct_change(21, fill_method=None) * 100,
        "gold_1m": raw["GOLD"].pct_change(21, fill_method=None) * 100,
        # stock-bond: corr of SPX returns with yield changes (+ = bonds hedge)
        "sb_corr": spx.pct_change(fill_method=None).rolling(63, min_periods=40).corr(y10.diff()),
    })
    labels = {"spx_dd": "S&P DD", "spx_1m": "S&P 1M", "vix": "VIX", "baa_3m": "Baa spread 3M",
              "y10_3m": "10Y 3M (bp)", "usd_1m": "USD 1M", "gold_1m": "Gold 1M", "sb_corr": "Stock-yield corr"}
    weights = pd.Series({"spx_dd": 1.5, "spx_1m": 1.0, "vix": 1.5, "baa_3m": 1.2, "y10_3m": 1.0,
                         "usd_1m": 0.8, "gold_1m": 0.8, "sb_corr": 0.8})
    f = feats.dropna()
    if len(f) < 500:
        return {"matches": [], "summary": None}
    today = f.iloc[-1]
    hist = f.loc[: f.index[-1] - pd.Timedelta(days=365)]
    z = (hist - hist.mean()) / hist.std()
    zt = (today - hist.mean()) / hist.std()
    dist = np.sqrt((((z - zt) ** 2) * weights).sum(axis=1))
    picked = []
    for d in dist.sort_values().index:
        if all(abs((d - p).days) > 120 for p in picked):
            picked.append(d)
        if len(picked) >= k:
            break
    fr = fwd_returns(spx, picked)
    by_date = {r["date"]: r for _, r in fr.iterrows()}
    nat = _native(spx).index
    matches = []
    for d in picked:
        j = nat.searchsorted(d)
        row = by_date.get(nat[j]) if j < len(nat) else None
        matches.append({"date": d.strftime("%Y-%m-%d"), "dist": float(dist.loc[d]),
                        "feat": {c: float(f.loc[d, c]) for c in f.columns},
                        "fwd": {kk: (float(row[kk]) if row is not None and pd.notna(row[kk]) else None)
                                for kk in list(HORIZONS) + ["maxDD6M"]}})
    return {"today": {c: float(today[c]) for c in f.columns}, "asof": f.index[-1].strftime("%Y-%m-%d"),
            "labels": labels, "matches": matches, "summary": _summ(fr)}


def run_all(raw, ind, scen) -> dict:
    out = {}
    for name, fn in (("episodes", lambda: episodes(raw, ind, scen)),
                     ("rules", lambda: rules(raw, ind)),
                     ("analogs", lambda: analogs(raw, ind))):
        try:
            out[name] = fn()
        except Exception as e:  # noqa: BLE001
            print(f"[backtest] {name} failed: {e!r}")
            out[name] = None
    return out
