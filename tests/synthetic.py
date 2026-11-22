"""Write synthetic raw data (random walks + a crash at the end) to test the
pipeline offline. Usage: python -m tests.synthetic && python -m pipeline.main --no-fetch --no-notify"""
import numpy as np
import pandas as pd

from pipeline import config as C, fetch

rng = np.random.default_rng(7)
idx = pd.bdate_range("1990-01-02", pd.Timestamp.today().normalize() - pd.Timedelta(days=2))
n = len(idx)


def walk(start, vol, drift=0.0003, crash=0.0):
    r = rng.normal(drift, vol, n)
    r[-25:] -= crash / 25
    return start * np.exp(np.cumsum(r))


def mean_rev(mu, sd, k=0.02, shock=0.0):
    x = np.empty(n); x[0] = mu
    for i in range(1, n):
        x[i] = x[i - 1] + k * (mu - x[i - 1]) + rng.normal(0, sd)
    x[-25:] += np.linspace(0, shock, 25)
    return x


y = pd.DataFrame(index=idx)
for k in C.YAHOO_SERIES:
    y[k] = walk(100, 0.012, crash=0.12 if k in ("SPX", "NDX", "SOX", "NVDA", "TWII", "TWOII", "TSMC", "KOSPI", "BTC", "GOLD") else 0.02)
y["VIX"] = np.abs(mean_rev(18, 1.2, shock=18))
y["VIX3M"] = np.abs(mean_rev(20, 0.8, shock=12))
y["MOVE"] = np.abs(mean_rev(95, 3, shock=15))
y.loc[: "2006-12-31", ["VIX3M", "CRWV", "BIZD", "RSP"]] = np.nan
y.loc[: "2024-03-01", "CRWV"] = np.nan

f = pd.DataFrame(index=idx)
f["HY_OAS"] = np.abs(mean_rev(4, 0.05, shock=0.4)); f.loc[: "2023-06-01", "HY_OAS"] = np.nan
f["IG_OAS"] = np.abs(mean_rev(1.2, 0.02)); f.loc[: "2023-06-01", "IG_OAS"] = np.nan
f["CCC_OAS"] = np.abs(mean_rev(9, 0.1)); f.loc[: "2023-06-01", "CCC_OAS"] = np.nan
f["BAA10Y"] = np.abs(mean_rev(2.2, 0.03, shock=0.3))
f["DGS2"] = np.abs(mean_rev(3.5, 0.05)); f["DGS10"] = np.abs(mean_rev(4.2, 0.04, shock=-0.25))
f["DFII10"] = mean_rev(1.5, 0.03); f["T10Y3M"] = mean_rev(1.0, 0.04); f["T5YIE"] = mean_rev(2.3, 0.02)
f["DFF"] = np.abs(mean_rev(3.0, 0.03)); f["SOFR"] = f["DFF"] + 0.02; f["IORB"] = f["DFF"] + 0.05
f.loc[: "2018-04-01", ["SOFR"]] = np.nan; f.loc[: "2021-07-28", ["IORB"]] = np.nan
f["SRF"] = 0.0; f["RRP"] = 100.0; f["RESERVES"] = 3000.0
f["STLFSI"] = mean_rev(-0.5, 0.05); f["NFCI"] = mean_rev(-0.4, 0.02)
f["ICSA"] = np.abs(mean_rev(230000, 3000)); f["USD_BROAD"] = walk(100, 0.003, 0)

tw = pd.DataFrame(index=idx[idx >= "2019-01-01"])
m = len(tw)
tw["tw_margin_amt"] = 3000 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, m))); tw.iloc[-20:, 0] *= np.linspace(1, 0.7, 20)
tw["tw_foreign"] = rng.normal(0, 80, m); tw["tw_adv"] = 400; tw["tw_dec"] = 500; tw["tw_limitup"] = 5
tw["tw_limitdown"] = np.where(np.arange(m) > m - 5, 130, 4); tw["tw_maint"] = np.nan
tw.iloc[-40:, tw.columns.get_loc("tw_maint")] = np.linspace(175, 156, 40)

y.to_csv(fetch.RAW / "yahoo.csv"); f.to_csv(fetch.RAW / "fred.csv"); tw.to_csv(fetch.RAW / "twse.csv")
print("synthetic data written", y.shape, f.shape, tw.shape)
