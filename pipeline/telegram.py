"""Telegram delivery. Chat ID: env TELEGRAM_CHAT_ID, else state/telegram.json,
else auto-detected from the latest message sent to the bot."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path

import requests

from . import config as C

STATE = Path(__file__).resolve().parent.parent / "state" / "telegram.json"
ICON = {"green": "🟢", "amber": "🟡", "red": "🔴", "na": "⚪", "info": "🔷"}


def _api(token, method, **kw):
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=kw, timeout=30)
    j = r.json()
    if not j.get("ok"):
        raise RuntimeError(f"Telegram {method}: {j}")
    return j["result"]


def chat_id(token) -> str | None:
    cid = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if cid:
        return cid
    if STATE.exists():
        cid = json.loads(STATE.read_text()).get("chat_id")
        if cid:
            return str(cid)
    ups = _api(token, "getUpdates", limit=50)
    for u in reversed(ups):
        msg = u.get("message") or u.get("channel_post") or {}
        if msg.get("chat", {}).get("id"):
            cid = str(msg["chat"]["id"])
            STATE.parent.mkdir(exist_ok=True)
            STATE.write_text(json.dumps({"chat_id": cid}))
            return cid
    return None


def e(x) -> str:
    return html.escape(str(x))


def build_message(D: dict, slot: str, url: str | None) -> str:
    cards = {c["id"]: c for c in D["cards"]}

    def v(i):
        c = cards.get(i)
        if not c or c["value"] is None:
            return "—"
        spec = C.IND_BY_ID[i]
        try:
            return spec["fmt"].format(c["value"]) + spec["unit"].replace("/11", "")
        except Exception:  # noqa: BLE001
            return str(c["value"])

    def px(k, digits=0):
        p = D["prices"].get(k)
        if not p:
            return f"{k} —"
        return f"{p['level']:,.{digits}f} ({p['chg1d']:+.1f}%)"

    title = "🌅 早盤簡報" if slot == "morning" else "🌆 晚間簡報"
    sc = D["scenarios"]
    top = max(sc["now"], key=sc["now"].get)
    L = [f"<b>{title}</b>　{e(D['updated'])}", ""]
    L.append("<b>情境分數</b>（0–100）")
    for k, meta in C.SCENARIOS.items():
        d = sc["delta_prev"].get(k)
        mark = " ◀ 最高" if k == top else ""
        L.append(f"{k} {e(meta['name'])}：<b>{sc['now'][k]:.0f}</b>" + (f"（{d:+.0f}）" if d is not None else "") + mark)
    if D["transitions"]:
        L += ["", "<b>燈號變化</b>"]
        for t in D["transitions"][:10]:
            L.append(f"{ICON[t['from']]}→{ICON[t['to']]} {e(C.IND_BY_ID[t['id']]['name'])}：{e(v(t['id']))}")
    reds = [c["id"] for c in D["cards"] if c["status"] == "red"]
    if reds:
        L += ["", f"<b>🔴 危險（{len(reds)}）</b>"]
        L.append("、".join(f"{e(C.IND_BY_ID[i]['name'])} {e(v(i))}" for i in reds[:12]))

    L += ["", "<b>美國</b>" if slot == "morning" else "<b>亞洲 / 台股</b>"]
    if slot == "morning":
        L.append(f"S&P {px('SPX')}｜NDX {px('NDX')}｜SOX {px('SOX')}")
        L.append(f"VIX {v('vix')}（期限 {v('vix_term')}）｜MOVE {v('move')}")
        L.append(f"HY {v('hy_oas')}（1M {v('hy_oas_chg')}）｜IG {v('ig_oas')}")
        L.append(f"10Y {v('dgs10')}｜升息定價 {v('fed_path')}｜SOFR−IORB {v('sofr_iorb')}")
        L.append(f"美元 1M {v('dollar_1m')}｜黃金 {px('GOLD')}｜BTC {px('BTC')}")
        L += ["", "<b>台股（昨日）</b>"]
    else:
        L.append(f"日經 {px('N225')}｜KOSPI {px('KOSPI', 0)}｜恒指 {px('HSI')}")
        L.append(f"人民幣 1M {v('cny_1m')}｜日圓壓力 {v('usdjpy_1m')}")
        L.append("")
    L.append(f"加權 {px('TWII')}｜櫃買 {px('TWOII', 2)}｜台積電 {px('TSMC')}")
    L.append(f"融資 {v('tw_margin')}（5日 {v('tw_margin_5d')}）｜維持率(估) {v('tw_maint')}")
    L.append(f"去槓桿進度 {v('tw_delever')}｜外資5日 {v('tw_foreign_5d')}｜跌停 {v('tw_limitdown')}")

    ai = D.get("ai")
    if ai:
        L += ["", f"<b>AI 資金鏈 {ICON[ai['light']]}</b>（{ai['n_bad']}/3 支柱轉壞，傳導 {ai['stage'] or 0:.0f}/4 環）"]
        L.append("　".join(f"{e(l['name'])} {l['r20']:+.0f}%" + ("✗" if l["hit"] else "") for l in ai["chain"] if l["r20"] is not None) + "（20日）")
        for k, nm in (("credit", "信用"), ("monetize", "變現"), ("capex", "capex")):
            if ai["reasons"][k]:
                L.append(f"🔴 {nm}：{e('、'.join(ai['reasons'][k][:4]))}")
        L.append(f"BBB {v('bbb_oas')}｜背離 {v('credit_eq_div')}｜BDC−HYG {v('bizd_hyg_1m')}｜ANT vs IPO {v('ant_vs_ipo')}")
        soon = [x for x in ai["calendar"] if x["days"] is not None and 0 <= x["days"] <= 14]
        if soon:
            L += ["", "<b>📅 未來兩週</b>"] + [f"{'❗' if x['days'] <= 3 else '•'} {e(x['date'][5:])}（{x['days']}天）{e(x['event'])}" for x in soon]

    an = (D.get("bt") or {}).get("analogs") or {}
    if an.get("matches"):
        s = an["summary"]
        dates = "、".join(m["date"][:7] for m in an["matches"][:4])
        med = lambda k: (s.get(k) or {}).get("median")  # noqa: E731
        L += ["", "<b>歷史類比</b>", f"最相似：{e(dates)}"]
        if med("6M") is not None:
            L.append(f"之後 S&P 中位數：3M {med('3M'):+.1f}%｜6M {med('6M'):+.1f}%｜6M 內最大跌幅 {med('maxDD6M'):+.1f}%")
    active = [r["name"] for r in ((D.get("bt") or {}).get("rules") or []) if r.get("active") and not r.get("baseline")]
    if active:
        L += ["", "<b>正在成立的回測條件</b>"] + [f"• {e(x)}" for x in active[:5]]
    if D.get("stale"):
        L += ["", "⚠️ 資料延遲：" + e("、".join(D["stale"]))]
    if url:
        L += ["", f'<a href="{e(url)}">打開儀表板 →</a>']
    return "\n".join(L)


def send(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("[Telegram] 未設定 TELEGRAM_BOT_TOKEN，略過推送")
        return False
    cid = chat_id(token)
    if not cid:
        print("[Telegram] 找不到 chat ID：請先在 Telegram 傳一則訊息給你的 bot")
        return False
    for chunk in [text[i:i + 3900] for i in range(0, len(text), 3900)]:
        _api(token, "sendMessage", chat_id=cid, text=chunk, parse_mode="HTML", disable_web_page_preview=True)
    print("[Telegram] 已推送")
    return True
