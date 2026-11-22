"""Turn raw series into indicator time series, statuses and scenario scores."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def daily_frame(fred: pd.DataFrame, yahoo: pd.DataFrame, twse: pd.DataFrame) -> pd.DataFrame:
    """One business-day frame. Market closes are forward-filled max 5 days so
    different holidays line up; weekly FRED series are forward-filled 10 days."""
    idx = pd.bdate_range(C.HISTORY_START, pd.Timestamp.today().normalize())
    parts = []
    for df, lim in ((yahoo, 5), (fred, 10), (twse, 3)):
        if df is not None and len(df):
            df = df[~df.index.duplicated(keep="last")].sort_index()
            parts.append(df.reindex(idx.union(df.index)).ffill(limit=lim).reindex(idx))
    raw = pd.concat(parts, axis=1)
    # drop trailing rows where nothing at all printed (e.g. today before open)
    last_real = max(d.dropna(how="all").index.max() for d in (yahoo, fred) if d is not None and len(d))
    return raw.loc[:last_real]


def _col(raw, name):
    return raw[name] if name in raw else pd.Series(np.nan, index=raw.index)


def _dd(s: pd.Series, win=252) -> pd.Series:
    return (s / s.rolling(win, min_periods=20).max() - 1) * 100


def _chg(s, n):
    return (s / s.shift(n) - 1) * 100


def _native(raw, name):
    """Series on its own trading days only (no forward-fill artefacts for returns)."""
    s = _col(raw, name)
    return s[s.diff().fillna(1) != 0] if s.notna().any() else s


def compute(raw: pd.DataFrame) -> pd.DataFrame:
    g = lambda n: _col(raw, n)  # noqa: E731
    out = pd.DataFrame(index=raw.index)

    # ---- global
    out["acwi_dd"] = _dd(g("ACWI"))
    r = lambda n: g(n).pct_change(fill_method=None)  # noqa: E731
    spy_r, tlt_r, gold_r = r("SPY"), r("TLT"), r("GOLD")
    all_down = ((spy_r < -0.01) & (tlt_r < 0) & (gold_r < 0)).astype(float)
    all_down[spy_r.isna() | tlt_r.isna() | gold_r.isna()] = np.nan
    out["everything_down"] = all_down.rolling(10, min_periods=5).sum()
    out["stock_bond_corr"] = spy_r.rolling(20, min_periods=15).corr(tlt_r)
    usd = g("USD_BROAD").combine_first(g("DXY"))
    out["dollar_1m"] = _chg(usd, 21)
    out["usdjpy_1m"] = _chg(g("USDJPY"), 21)
    out["gold_1m"] = _chg(g("GOLD"), 21)
    out["btc_dd"] = _dd(g("BTC"))
    out["copper_gold"] = _chg(g("COPPER") / g("GOLD"), 63)
    out["kospi_dd"] = _dd(g("KOSPI"))
    out["n225_dd"] = _dd(g("N225"))
    out["hsi_dd"] = _dd(g("HSI"))
    out["cny_1m"] = _chg(g("USDCNY"), 21)

    # ---- US credit
    out["hy_oas"] = g("HY_OAS")
    out["hy_oas_chg"] = (g("HY_OAS") - g("HY_OAS").shift(21)) * 100
    out["ig_oas"] = g("IG_OAS")
    out["ccc_oas"] = g("CCC_OAS")
    out["baa10y"] = g("BAA10Y")
    out["hyg_lqd_1m"] = _chg(g("HYG") / g("LQD"), 21)
    out["bizd_dd"] = _dd(g("BIZD"))
    out["kre_dd"] = _dd(g("KRE"))

    # ---- funding
    out["sofr_iorb"] = (g("SOFR") - g("IORB")) * 100
    out["srf"] = g("SRF")
    out["stlfsi"] = g("STLFSI")
    out["nfci"] = g("NFCI")
    out["move"] = g("MOVE")

    # ---- vol
    out["vix"] = g("VIX")
    out["vix_term"] = g("VIX") / g("VIX3M")

    # ---- policy / growth
    out["fed_path"] = (g("DGS2") - g("DFF")) * 100
    out["real10"] = g("DFII10")
    out["dgs10"] = g("DGS10")
    out["breakeven"] = g("T5YIE")
    out["curve"] = g("T10Y3M") * 100
    out["claims"] = g("ICSA").rolling(20, min_periods=5).mean() / 1000

    # ---- internals / AI
    out["spx_dd"] = _dd(g("SPX"))
    out["ndx_dd"] = _dd(g("NDX"))
    above = pd.DataFrame({s: (g(s) > g(s).rolling(200, min_periods=150).mean()).where(g(s).notna())
                          for s in C.SECTOR_ETFS})
    out["sectors_200"] = above.sum(axis=1, min_count=8)
    out["rsp_spy_3m"] = _chg(g("RSP"), 63) - _chg(g("SPY"), 63)
    out["sox_dd"] = _dd(g("SOX"))
    out["ai_dd"] = pd.DataFrame({s: _dd(g(s)) for s in C.AI_BASKET}).mean(axis=1, skipna=True)
    out["orcl_dd"] = _dd(g("ORCL"))
    out["crwv_dd"] = _dd(g("CRWV"))

    # ---- AI funding chain
    basket_dd = lambda names: pd.DataFrame({n: _dd(g(n)) for n in names}).mean(axis=1, skipna=True)  # noqa: E731
    basket_ret = lambda names, n: pd.DataFrame({k: _chg(g(k), n) for k in names}).mean(axis=1, skipna=True)  # noqa: E731
    out["bbb_oas"] = g("BBB_OAS")
    hyg20 = _chg(g("HYG"), 20)
    neo20 = basket_ret(C.NEOCLOUD, 20)
    div = ((hyg20 < -0.5) & (neo20 > 5)).astype(float).where(hyg20.notna() & neo20.notna())
    out["credit_eq_div"] = div.rolling(10, min_periods=5).sum()
    out["bizd_hyg_1m"] = _chg(g("BIZD"), 21) - _chg(g("HYG"), 21)
    out["owl_dd"] = _dd(g("OWL"))
    out["ai_chain_stage"] = chain_stage(raw)
    out["neocloud_dd"] = basket_dd(C.NEOCLOUD)
    out["upstream_dd"] = basket_dd(C.UPSTREAM)
    out["hyper_dd"] = basket_dd(C.HYPERSCALERS)
    out["tw_chain_dd"] = basket_dd(C.TW_CHAIN)
    out["power_dd"] = basket_dd(C.POWER)
    out["ant_vs_ipo"] = (g("ANT") / C.ANT_IPO_PRICE - 1) * 100
    hyper_ew = pd.DataFrame({k: g(k) / g(k).dropna().iloc[0] for k in C.HYPERSCALERS if g(k).notna().any()}).mean(axis=1)
    out["up_vs_hyper"] = _chg(g("SMH") / hyper_ew, 63)

    # ---- Taiwan
    out["twii_dd"] = _dd(g("TWII"))
    out["twoii_dd"] = _dd(g("TWOII"))
    out["tsmc_dd"] = _dd(g("TSMC"))
    m = g("tw_margin_amt")
    out["tw_margin"] = m
    out["tw_margin_5d"] = _chg(m, 5)
    out["tw_delever"] = delever_ratio(g("TWII"), m)
    out["tw_maint"] = g("tw_maint")
    out["tw_foreign_5d"] = g("tw_foreign").rolling(5, min_periods=4).sum()
    out["tw_limitdown"] = g("tw_limitdown")
    out["twd_1m"] = _chg(g("USDTWD"), 21)
    return out


def chain_stage(raw: pd.DataFrame, n: int = 20) -> pd.Series:
    """How many links of the chain, counted in order from the weakest, have
    cracked (20-day basket return below the link's threshold)."""
    stage = pd.Series(0.0, index=raw.index)
    still = pd.Series(True, index=raw.index)
    any_data = pd.Series(False, index=raw.index)
    for _, names, th in C.CHAIN_LINKS:
        r = pd.DataFrame({k: _chg(raw[k], n) for k in names if k in raw}).mean(axis=1, skipna=True)
        any_data |= r.notna()
        hit = (r <= th).fillna(False)
        still &= hit
        stage += still.astype(float)
    return stage.where(any_data)


def chain_detail(raw: pd.DataFrame) -> list[dict]:
    out = []
    for name, names, th in C.CHAIN_LINKS:
        cols = [k for k in names if k in raw and raw[k].notna().any()]
        if not cols:
            out.append(dict(name=name, members=names, r5=None, r20=None, dd=None, th=th, hit=False))
            continue
        r5 = float(pd.DataFrame({k: _chg(raw[k], 5) for k in cols}).mean(axis=1).iloc[-1])
        r20 = float(pd.DataFrame({k: _chg(raw[k], 20) for k in cols}).mean(axis=1).iloc[-1])
        dd = float(pd.DataFrame({k: _dd(raw[k]) for k in cols}).mean(axis=1).iloc[-1])
        out.append(dict(name=name, members=names, r5=r5, r20=r20, dd=dd, th=th, hit=bool(r20 <= th)))
    return out


def delever_ratio(index: pd.Series, margin: pd.Series, win=252) -> pd.Series:
    """(margin decline since the index's 52w peak) / (index decline since that peak).
    Only meaningful when the index is down >= 8%."""
    out = pd.Series(np.nan, index=index.index)
    idx_vals, m_vals = index.values, margin.values
    for i in range(len(index)):
        lo = max(0, i - win + 1)
        w = idx_vals[lo:i + 1]
        if np.all(np.isnan(w)) or np.isnan(idx_vals[i]) or np.isnan(m_vals[i]):
            continue
        p = lo + int(np.nanargmax(w))
        dd = idx_vals[i] / idx_vals[p] - 1
        mp = m_vals[p]
        if dd > -0.08 or np.isnan(mp):
            continue
        out.iloc[i] = (m_vals[i] / mp - 1) / dd
    return out


# ---------------------------------------------------------------- statuses
def thresholds(spec: dict, s: pd.Series) -> tuple[float, float]:
    if spec["mode"] == "abs":
        return spec["amber"], spec["red"]
    h = s.dropna()
    if len(h) < 250:
        return np.nan, np.nan
    return float(h.quantile(spec["amber"])), float(h.quantile(spec["red"]))


def stress_value(spec, x, amber, red) -> float:
    """0 = calm, 0.5 = at amber, 1 = at/through red (continuous)."""
    if x is None or np.isnan(x) or np.isnan(amber) or np.isnan(red):
        return np.nan
    d = spec["dir"]
    a, r_, v = amber * d, red * d, x * d
    span = abs(r_ - a) or 1.0
    if v < a:
        return 0.3 * max(0.0, 1 - (a - v) / (2 * span))
    if r_ == a:
        return 1.0
    return float(min(1.0, 0.5 + 0.5 * (v - a) / (r_ - a)))


def status_of(stress: float) -> str:
    if np.isnan(stress):
        return "na"
    return "red" if stress >= 0.999 else "amber" if stress >= 0.5 else "green"


def stress_frame(ind: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Historical stress for every indicator (pct thresholds use expanding
    history to avoid look-ahead) + today's thresholds."""
    st = pd.DataFrame(index=ind.index)
    th = {}
    for spec in C.IND:
        s = ind[spec["id"]]
        if spec["mode"] == "info":
            st[spec["id"]] = np.nan
            th[spec["id"]] = (np.nan, np.nan)
            continue
        if spec["mode"] == "abs":
            a, r_ = spec["amber"], spec["red"]
            st[spec["id"]] = [stress_value(spec, x, a, r_) for x in s.values]
            th[spec["id"]] = (a, r_)
        else:
            h = s.dropna()
            if len(h) < 250:
                st[spec["id"]] = np.nan
                th[spec["id"]] = (np.nan, np.nan)
                continue
            pr = h.expanding(min_periods=250).rank(pct=True)
            lo_q, hi_q = spec["amber"], spec["red"]
            # map percentile to stress on the same 0-1 scale
            if spec["dir"] > 0:
                val = np.where(pr < lo_q, 0.5 * pr / lo_q * 0.6,
                               np.minimum(1, 0.5 + 0.5 * (pr - lo_q) / (hi_q - lo_q)))
            else:
                val = np.where(pr > lo_q, 0.5 * (1 - pr) / (1 - lo_q) * 0.6,
                               np.minimum(1, 0.5 + 0.5 * (lo_q - pr) / (lo_q - hi_q)))
            st[spec["id"]] = pd.Series(val, index=h.index).reindex(ind.index)
            th[spec["id"]] = thresholds(spec, s)
    return st, th


def group_scores(st: pd.DataFrame) -> pd.DataFrame:
    groups = {}
    for spec in C.IND:
        if spec["mode"] == "info":
            continue
        groups.setdefault(spec["grp"], []).append(spec["id"])
    return pd.DataFrame({g: st[ids].mean(axis=1, skipna=True) for g, ids in groups.items()})


def scenario_scores(gs: pd.DataFrame, manual: dict | None = None) -> pd.DataFrame:
    f = lambda k: gs[k].fillna(0) if k in gs else 0  # noqa: E731
    eq, cr, fu, xa = f("equity"), f("credit"), f("funding"), f("xasset")
    ai, po, gr = f("ai"), f("policy"), f("growth")
    aicr, aich = f("aicredit"), f("aichain")
    capex_cut = 1.0 if (manual or {}).get("capex_cut_announced") else 0.0
    sc = pd.DataFrame(index=gs.index)
    sc["A"] = eq * (1 - 0.8 * cr) * (1 - 0.8 * fu)
    sc["B"] = (0.30 * ai + 0.15 * aich + 0.25 * po + 0.30 * gr) * 0.85 + 0.15 * capex_cut + 0.15 * eq * ai
    sc["C"] = 0.45 * cr + 0.25 * aicr + 0.15 * aich * cr + 0.15 * cr * eq
    sc["D"] = 0.50 * fu + 0.35 * xa + 0.15 * fu * xa
    return (sc.clip(0, 1) * 100).round(1)
