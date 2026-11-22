"""Data fetchers. Each source writes to data/raw and merges incrementally,
so history accumulates and a failed day never wipes earlier data."""
from __future__ import annotations

import io
import json
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from . import config as C

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
LOG: list[str] = []          # human-readable fetch log, shown on the dashboard


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.append(msg)


def _get(url, params=None, tries=3, timeout=30, sleep=2.0):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(sleep * (i + 1))
    raise RuntimeError(f"{url} failed: {last}")


def _merge_save(path: Path, new: pd.DataFrame) -> pd.DataFrame:
    if path.exists():
        old = pd.read_csv(path, index_col=0, parse_dates=True)
        new = new.combine_first(old) if not new.empty else old
        # newest fetch wins for overlapping cells
    new = new.sort_index()
    new = new[~new.index.duplicated(keep="last")]
    new.to_csv(path)
    return new


# ---------------------------------------------------------------- FRED
def fetch_fred() -> pd.DataFrame:
    key = os.environ.get("FRED_API_KEY", "").strip()
    cols = {}
    for name, sid in C.FRED_SERIES.items():
        try:
            if key:
                r = _get("https://api.stlouisfed.org/fred/series/observations",
                         params=dict(series_id=sid, api_key=key, file_type="json",
                                     observation_start=C.HISTORY_START))
                obs = r.json()["observations"]
                s = pd.Series({pd.Timestamp(o["date"]): o["value"] for o in obs})
            else:
                r = _get("https://fred.stlouisfed.org/graph/fredgraph.csv", params=dict(id=sid))
                df = pd.read_csv(io.StringIO(r.text))
                s = pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0]))
            s = pd.to_numeric(s.replace(".", None), errors="coerce").dropna()
            cols[name] = s
        except Exception as e:  # noqa: BLE001
            log(f"[FRED] {name} ({sid}) 失敗: {e}")
    df = pd.DataFrame(cols)
    out = _merge_save(RAW / "fred.csv", df)
    log(f"[FRED] {len(cols)}/{len(C.FRED_SERIES)} 個 series，最新 {out.index.max().date() if len(out) else '-'}")
    return out


# ---------------------------------------------------------------- Yahoo / stooq
def _yahoo_chart(sym: str, start: datetime) -> pd.Series:
    p1 = int(start.replace(tzinfo=timezone.utc).timestamp())
    p2 = int(time.time()) + 86400
    for host in ("query1", "query2"):
        try:
            r = _get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}",
                     params=dict(period1=p1, period2=p2, interval="1d", events="history"), tries=2)
            res = r.json()["chart"]["result"][0]
            ts = res.get("timestamp") or []
            q = res["indicators"]
            closes = (q.get("adjclose") or [{}])[0].get("adjclose") or q["quote"][0]["close"]
            gmt = res["meta"].get("gmtoffset", 0)
            idx = pd.to_datetime([t + gmt for t in ts], unit="s").normalize()
            return pd.Series(closes, index=idx, dtype="float64").dropna()
        except Exception as e:  # noqa: BLE001
            err = e
    raise RuntimeError(err)


def _stooq(sym: str) -> pd.Series:
    r = _get("https://stooq.com/q/d/l/", params=dict(s=sym, i="d"), tries=2)
    df = pd.read_csv(io.StringIO(r.text))
    return pd.Series(df["Close"].values, index=pd.to_datetime(df["Date"]))


def fetch_yahoo() -> pd.DataFrame:
    path = RAW / "yahoo.csv"
    have = pd.read_csv(path, index_col=0, parse_dates=True) if path.exists() else pd.DataFrame()
    cols, failed = {}, []
    for name, sym in C.YAHOO_SERIES.items():
        # incremental: 45 days if we already have the column, else full history
        if name in have and have[name].notna().sum() > 300:
            start = datetime.now() - timedelta(days=45)
        else:
            start = datetime.fromisoformat(C.HISTORY_START)
        try:
            cols[name] = _yahoo_chart(sym, start)
        except Exception as e:  # noqa: BLE001
            fb = C.STOOQ_FALLBACK.get(name)
            if fb:
                try:
                    cols[name] = _stooq(fb)
                    log(f"[Yahoo] {name} 改用 stooq")
                    continue
                except Exception as e2:  # noqa: BLE001
                    e = e2
            failed.append(name)
            log(f"[Yahoo] {name} ({sym}) 失敗: {e}")
        time.sleep(0.4)
    out = _merge_save(path, pd.DataFrame(cols))
    log(f"[Yahoo] {len(cols)}/{len(C.YAHOO_SERIES)} 檔，最新 {out.index.max().date() if len(out) else '-'}")
    return out


# ---------------------------------------------------------------- TWSE
TWSE = "https://www.twse.com.tw/rwd/zh"
_num = re.compile(r"-?[\d,]+(?:\.\d+)?")


def _n(x) -> float | None:
    m = _num.search(str(x))
    return float(m.group().replace(",", "")) if m else None


def _twse_json(path: str, **params) -> dict | None:
    params["response"] = "json"
    r = _get(f"{TWSE}/{path}", params=params, tries=3, sleep=4)
    j = r.json()
    if str(j.get("stat", "")).upper() != "OK":
        return None
    return j


def _tables(j: dict):
    """Yield (title, fields, rows) across TWSE's old and new JSON layouts."""
    if "tables" in j:
        for t in j["tables"]:
            yield t.get("title", ""), t.get("fields", []), t.get("data", [])
    for k, v in j.items():
        if k.endswith("List") or k == "data" or re.fullmatch(r"data\d+", k):
            fk = k.replace("List", "Fields") if k.endswith("List") else k.replace("data", "fields")
            yield k, j.get(fk, []), v


def twse_margin(d: date) -> dict:
    j = _twse_json("marginTrading/MI_MARGN", date=d.strftime("%Y%m%d"), selectType="MS")
    if not j:
        return {}
    for _, _, rows in _tables(j):
        for row in rows:
            if row and "融資金額" in str(row[0]):
                return {"tw_margin_amt": _n(row[-1]) / 1e5}   # 仟元 -> 億元
    return {}


def twse_foreign(d: date) -> dict:
    j = _twse_json("fund/BFI82U", type="day", dayDate=d.strftime("%Y%m%d"))
    if not j:
        return {}
    tot = 0.0
    hit = False
    for _, _, rows in _tables(j):
        for row in rows:
            if row and "外資" in str(row[0]):
                v = _n(row[-1])
                if v is not None:
                    tot += v
                    hit = True
    return {"tw_foreign": tot / 1e8} if hit else {}            # 元 -> 億元


def twse_breadth(d: date) -> dict:
    j = _twse_json("afterTrading/MI_INDEX", date=d.strftime("%Y%m%d"), type="MS")
    if not j:
        return {}
    out = {}
    for _, _, rows in _tables(j):
        for row in rows:
            if not row or len(row) < 2:
                continue
            label, cell = str(row[0]), str(row[1])
            nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+", cell)]
            if label.startswith("上漲") and nums:
                out["tw_adv"] = nums[0]
                out["tw_limitup"] = nums[1] if len(nums) > 1 else None
            elif label.startswith("下跌") and nums:
                out["tw_dec"] = nums[0]
                out["tw_limitdown"] = nums[1] if len(nums) > 1 else None
    return out


def twse_maintenance(d: date) -> dict:
    """Market-wide TWSE margin maintenance ratio estimate:
    sum(margin balance shares x close) / margin loan amount."""
    ds = d.strftime("%Y%m%d")
    jm = _twse_json("marginTrading/MI_MARGN", date=ds, selectType="ALL")
    time.sleep(3)
    jp = _twse_json("afterTrading/MI_INDEX", date=ds, type="ALLBUT0999")
    if not jm or not jp:
        return {}
    bal, loan = {}, None
    for title, fields, rows in _tables(jm):
        for row in rows:
            if row and "融資金額" in str(row[0]):
                loan = _n(row[-1]) * 1000                      # 仟元 -> 元
            elif row and re.fullmatch(r"\d{4,6}[A-Z]?", str(row[0]).strip()) and len(row) > 6:
                v = _n(row[6])
                if v:
                    bal[str(row[0]).strip()] = v * 1000         # 張 -> 股
    close = {}
    for title, fields, rows in _tables(jp):
        if not fields or "收盤價" not in fields:
            continue
        ci = fields.index("收盤價")
        for row in rows:
            v = _n(row[ci]) if len(row) > ci else None
            if v:
                close[str(row[0]).strip()] = v
    if not loan or len(bal) < 200:
        return {}
    mv = sum(sh * close[c] for c, sh in bal.items() if c in close)
    return {"tw_maint": mv / loan * 100}


def fetch_twse(trading_days: list[date], budget_s: int = 420, maint_days: int = 40) -> pd.DataFrame:
    """Fill missing TWSE fields, newest first, within a time budget.
    Older dates are backfilled a little more on every run."""
    path = RAW / "twse.csv"
    df = pd.read_csv(path, index_col=0, parse_dates=True) if path.exists() else pd.DataFrame()
    for c in ["tw_margin_amt", "tw_foreign", "tw_adv", "tw_dec", "tw_limitup", "tw_limitdown", "tw_maint"]:
        if c not in df:
            df[c] = pd.Series(dtype="float64")
    tried_path = RAW / "twse_tried.json"
    tried = json.loads(tried_path.read_text()) if tried_path.exists() else {}
    t0 = time.time()
    days = sorted(set(trading_days), reverse=True)
    today = date.today()
    n_calls = 0
    for i, d in enumerate(days):
        if time.time() - t0 > budget_s:
            log(f"[TWSE] 時間預算用完，下次繼續補歷史（已到 {d}）")
            break
        ts = pd.Timestamp(d)
        row = df.loc[ts] if ts in df.index else None
        recent = (today - d).days <= 7
        jobs = []
        def need(col):
            return row is None or pd.isna(row.get(col))
        if need("tw_margin_amt"):
            jobs.append(("margin", twse_margin))
        if (today - d).days <= 800 and need("tw_foreign"):
            jobs.append(("foreign", twse_foreign))
        if (today - d).days <= 800 and need("tw_limitdown"):
            jobs.append(("breadth", twse_breadth))
        if i < maint_days and need("tw_maint"):
            jobs.append(("maint", twse_maintenance))
        for key, fn in jobs:
            tkey = f"{d}:{key}"
            if not recent and tried.get(tkey, 0) >= 2:
                continue   # gave up on this date/field after 2 empty answers
            try:
                vals = fn(d)
                n_calls += 1
            except Exception as e:  # noqa: BLE001
                log(f"[TWSE] {d} {key} 失敗: {e}")
                vals = {}
                time.sleep(10)
            if vals:
                for k, v in vals.items():
                    df.loc[ts, k] = v
            else:
                tried[tkey] = tried.get(tkey, 0) + 1
            time.sleep(3.1)   # TWSE rate limit ~3 req / 5s
    df = df.sort_index()
    df.to_csv(path)
    tried_path.write_text(json.dumps(tried))
    have = df["tw_margin_amt"].notna().sum()
    log(f"[TWSE] 本次 {n_calls} 次請求；融資歷史 {have} 天（自 {df['tw_margin_amt'].dropna().index.min().date() if have else '-'}）")
    return df
