"""Series sources and indicator definitions.

Every indicator is a daily time series, so the same definition drives today's
reading, its historical percentile, the backtest, and the scenario scores.
"""

HISTORY_START = "1990-01-01"
TZ = "Asia/Shanghai"

# ---------------------------------------------------------------- raw series
FRED_SERIES = {
    "HY_OAS": "BAMLH0A0HYM2",    # ICE BofA US HY OAS (FRED only keeps ~3y)
    "IG_OAS": "BAMLC0A0CM",      # ICE BofA US IG OAS
    "CCC_OAS": "BAMLH0A3HYC",    # ICE BofA CCC & lower OAS
    "BAA10Y": "BAA10Y",          # Moody's Baa - 10y (long history credit proxy)
    "DGS2": "DGS2",
    "DGS10": "DGS10",
    "DFII10": "DFII10",          # 10y real yield
    "T10Y3M": "T10Y3M",
    "T5YIE": "T5YIE",            # 5y breakeven
    "DFF": "DFF",                # effective fed funds
    "SOFR": "SOFR",
    "IORB": "IORB",
    "SRF": "RPONTSYD",           # Fed overnight repo ops (standing repo take-up), $bn
    "RRP": "RRPONTSYD",
    "RESERVES": "WRESBAL",
    "STLFSI": "STLFSI4",
    "NFCI": "NFCI",
    "ICSA": "ICSA",
    "USD_BROAD": "DTWEXBGS",
}

YAHOO_SERIES = {
    "SPX": "^GSPC", "NDX": "^NDX", "SOX": "^SOX", "VIX": "^VIX", "VIX3M": "^VIX3M",
    "MOVE": "^MOVE", "SPY": "SPY", "RSP": "RSP", "TLT": "TLT", "HYG": "HYG", "LQD": "LQD",
    "GOLD": "GC=F", "COPPER": "HG=F", "BTC": "BTC-USD", "DXY": "DX-Y.NYB", "ACWI": "ACWI",
    "USDJPY": "JPY=X", "USDCNY": "CNY=X", "USDTWD": "TWD=X",
    "N225": "^N225", "KOSPI": "^KS11", "HSI": "^HSI", "SSE": "000001.SS",
    "TWII": "^TWII", "TWOII": "^TWOII", "TSMC": "2330.TW",
    "NVDA": "NVDA", "MSFT": "MSFT", "META": "META", "GOOGL": "GOOGL", "AMZN": "AMZN",
    "ORCL": "ORCL", "CRWV": "CRWV", "BIZD": "BIZD", "KRE": "KRE",
    "XLK": "XLK", "XLF": "XLF", "XLE": "XLE", "XLV": "XLV", "XLY": "XLY", "XLP": "XLP",
    "XLI": "XLI", "XLB": "XLB", "XLU": "XLU", "XLRE": "XLRE", "XLC": "XLC",
}

# stooq fallback symbols for the most important tickers
STOOQ_FALLBACK = {
    "SPX": "^spx", "NDX": "^ndx", "SPY": "spy.us", "RSP": "rsp.us", "TLT": "tlt.us",
    "HYG": "hyg.us", "LQD": "lqd.us", "GOLD": "gc.f", "COPPER": "hg.f", "BTC": "btcusd",
    "DXY": "dx.f", "ACWI": "acwi.us", "USDJPY": "usdjpy", "USDCNY": "usdcny",
    "USDTWD": "usdtwd", "N225": "^nkx", "HSI": "^hsi", "NVDA": "nvda.us",
    "MSFT": "msft.us", "META": "meta.us", "GOOGL": "googl.us", "AMZN": "amzn.us",
    "ORCL": "orcl.us", "BIZD": "bizd.us", "KRE": "kre.us",
}

SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
AI_BASKET = ["NVDA", "MSFT", "META", "GOOGL", "AMZN", "ORCL"]

# ---------------------------------------------------------------- indicators
# dir  +1: higher = more stress, -1: lower = more stress
# mode "abs": amber/red are absolute levels; "pct": amber/red are history percentiles
# fmt: python format for display; unit shown after value
IND = [
    # ---- global / cross-asset
    dict(id="acwi_dd", sec="global", grp="equity", name="全球股市回撤 (ACWI)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20,
         note="距 52 週高點跌幅"),
    dict(id="everything_down", sec="global", grp="xasset", name="股債金同跌天數 (10日)", unit="天", fmt="{:.0f}", dir=1, mode="abs", amber=1, red=3,
         note="SPY 跌>1% 且 TLT、黃金同日下跌；2020/3 型「什麼都賣」偵測"),
    dict(id="stock_bond_corr", sec="global", grp="xasset", name="股債相關性 (20日)", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=0.3, red=0.6,
         note="SPY 與 TLT 報酬相關；正值代表債券失去避險功能"),
    dict(id="dollar_1m", sec="global", grp="xasset", name="美元 1 個月變化", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97,
         note="美元急漲 = 全球美元荒"),
    dict(id="usdjpy_1m", sec="global", grp="xasset", name="日圓套利壓力 (USDJPY 1M)", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.15, red=0.04,
         note="日圓急升 = 套利交易平倉（2024/8 型）"),
    dict(id="gold_1m", sec="global", grp="xasset", name="黃金 1 個月報酬", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.10, red=0.03,
         note="避險資產被賣 = 去槓桿/追保"),
    dict(id="btc_dd", sec="global", grp="equity", name="比特幣回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-25, red=-45,
         note="槓桿與風險偏好溫度計"),
    dict(id="copper_gold", sec="global", grp="growth", name="銅金比 3 個月變化", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.15, red=0.05,
         note="下降 = 市場定價增長放緩"),
    dict(id="kospi_dd", sec="global", grp="asia", name="韓股回撤 (KOSPI)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note="亞洲 AI 交易核心"),
    dict(id="n225_dd", sec="global", grp="asia", name="日股回撤 (Nikkei)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="hsi_dd", sec="global", grp="asia", name="港股回撤 (恒指)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="cny_1m", sec="global", grp="asia", name="人民幣 1 個月變化 (USDCNY)", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97, note="正值 = 人民幣貶值"),

    # ---- US: credit
    dict(id="hy_oas", sec="us", grp="credit", name="高收益債利差 (HY OAS)", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=4.0, red=5.0,
         note="2018Q4 高點 ~5.3%、2020/3 ~10.9%、2008 ~19.9%"),
    dict(id="hy_oas_chg", sec="us", grp="credit", name="HY 利差 1 個月變化", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=50, red=120, note="速度比水準更重要"),
    dict(id="ig_oas", sec="us", grp="credit", name="投資級利差 (IG OAS)", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=1.3, red=1.7,
         note="AI 基建的債大多在投資級（Oracle、hyperscaler）"),
    dict(id="ccc_oas", sec="us", grp="credit", name="CCC 級利差", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=9.0, red=12.0, note="最弱借款人"),
    dict(id="baa10y", sec="us", grp="credit", name="Baa 公司債利差 (長歷史)", unit="%", fmt="{:.2f}", dir=1, mode="pct", amber=0.80, red=0.95,
         note="1986 年起的長歷史信用指標，供回測"),
    dict(id="hyg_lqd_1m", sec="us", grp="credit", name="HYG/LQD 1 個月變化", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.10, red=0.03, note="垃圾債相對投資級"),
    dict(id="bizd_dd", sec="us", grp="credit", name="BDC 回撤 (私募信貸代理)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20,
         note="私募信貸一季才重估，BDC 股價是最快的訊號"),
    dict(id="kre_dd", sec="us", grp="credit", name="區域銀行回撤 (KRE)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-25, note="2023 SVB 型訊號"),

    # ---- US: funding
    dict(id="sofr_iorb", sec="us", grp="funding", name="SOFR − IORB", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=0, red=10,
         note="正值 = 回購市場缺錢（2019/9 型）"),
    dict(id="srf", sec="us", grp="funding", name="Fed 常備回購使用量", unit="$bn", fmt="{:.1f}", dir=1, mode="abs", amber=1, red=10, note=">0 代表有機構向 Fed 借急錢"),
    dict(id="stlfsi", sec="us", grp="funding", name="聖路易金融壓力指數", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=0, red=1.5, note="0 = 歷史平均（週頻）"),
    dict(id="nfci", sec="us", grp="funding", name="芝加哥金融狀況 (NFCI)", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=-0.2, red=0.2, note=">0 = 緊於平均（週頻）"),
    dict(id="move", sec="us", grp="funding", name="美債波動率 (MOVE)", unit="", fmt="{:.0f}", dir=1, mode="abs", amber=110, red=140, note="債市流動性壓力"),

    # ---- US: vol
    dict(id="vix", sec="us", grp="equity", name="VIX", unit="", fmt="{:.1f}", dir=1, mode="abs", amber=25, red=35, note=""),
    dict(id="vix_term", sec="us", grp="equity", name="VIX 期限結構 (VIX/VIX3M)", unit="", fmt="{:.2f}", dir=1, mode="abs", amber=1.0, red=1.1,
         note=">1 倒掛 = 恐慌當下；回到 <0.9 = 恐慌消退"),

    # ---- US: policy / rates
    dict(id="fed_path", sec="us", grp="policy", name="市場定價升息 (2Y − FFR)", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=25, red=60,
         note="正值 = 市場預期還要升息"),
    dict(id="real10", sec="us", grp="policy", name="10 年實質利率", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=2.0, red=2.5, note="高實質利率壓估值"),
    dict(id="dgs10", sec="us", grp="policy", name="10 年美債殖利率", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=4.75, red=5.25, note=""),
    dict(id="breakeven", sec="us", grp="policy", name="5 年通膨預期", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=2.7, red=3.1, note="Fed 被綁住的程度"),
    dict(id="curve", sec="us", grp="growth", name="殖利率曲線 (10Y − 3M)", unit="bp", fmt="{:+.0f}", dir=-1, mode="abs", amber=0, red=-75, note="倒掛 = 衰退訊號"),
    dict(id="claims", sec="us", grp="growth", name="初領失業金 (4週均)", unit="k", fmt="{:.0f}", dir=1, mode="abs", amber=260, red=300, note=""),

    # ---- US: internals / AI
    dict(id="spx_dd", sec="us", grp="equity", name="S&P 500 回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="ndx_dd", sec="us", grp="equity", name="Nasdaq 100 回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="sectors_200", sec="us", grp="internals", name="站上 200 日線的板塊", unit="/11", fmt="{:.0f}", dir=-1, mode="abs", amber=6, red=3, note="市場廣度"),
    dict(id="rsp_spy_3m", sec="us", grp="internals", name="等權重 vs 市值權重 (3M)", unit="%", fmt="{:+.1f}", dir=1, mode="abs", amber=4, red=8,
         note="正值大 = 龍頭股被賣、資金撤出 AI 權值"),
    dict(id="sox_dd", sec="us", grp="ai", name="費城半導體回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-20, red=-35, note=""),
    dict(id="ai_dd", sec="us", grp="ai", name="AI 龍頭籃子平均回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30,
         note="NVDA、MSFT、META、GOOGL、AMZN、ORCL"),
    dict(id="orcl_dd", sec="us", grp="ai", name="Oracle 回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-30, red=-50, note="舉債建 AI 的代表"),
    dict(id="crwv_dd", sec="us", grp="ai", name="CoreWeave 回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-40, red=-65, note="AI 算力租賃 + 高槓桿"),

    # ---- Taiwan
    dict(id="twii_dd", sec="tw", grp="tw", name="加權指數回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="twoii_dd", sec="tw", grp="tw", name="櫃買指數回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-12, red=-25, note=""),
    dict(id="tsmc_dd", sec="tw", grp="tw", name="台積電回撤", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30, note=""),
    dict(id="tw_margin", sec="tw", grp="tw", name="上市融資餘額", unit="億", fmt="{:,.0f}", dir=1, mode="pct", amber=0.85, red=0.97, note="槓桿水位"),
    dict(id="tw_margin_5d", sec="tw", grp="tw", name="融資 5 日變化", unit="%", fmt="{:+.1f}", dir=-1, mode="abs", amber=-5, red=-10, note="快速下降 = 斷頭潮"),
    dict(id="tw_delever", sec="tw", grp="tw", name="去槓桿進度 (融資降幅 ÷ 指數跌幅)", unit="x", fmt="{:.2f}", dir=-1, mode="abs", amber=0.8, red=0.5,
         note="自指數高點起算；>1 = 融資砍得比指數多（股魚指標，見回測頁驗證）"),
    dict(id="tw_maint", sec="tw", grp="tw", name="上市融資維持率 (估)", unit="%", fmt="{:.0f}", dir=-1, mode="abs", amber=160, red=145,
         note="融資餘額市值 ÷ 融資金額；130% 為追繳線"),
    dict(id="tw_foreign_5d", sec="tw", grp="tw", name="外資 5 日買賣超", unit="億", fmt="{:+,.0f}", dir=-1, mode="pct", amber=0.10, red=0.03, note=""),
    dict(id="tw_limitdown", sec="tw", grp="tw", name="上市跌停家數", unit="家", fmt="{:.0f}", dir=1, mode="abs", amber=40, red=120, note="鎖跌停 = 市場流動性枯竭"),
    dict(id="twd_1m", sec="tw", grp="tw", name="新台幣 1 個月變化 (USDTWD)", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97, note="正值 = 台幣貶、資金外流"),
]
IND_BY_ID = {d["id"]: d for d in IND}

GROUP_NAMES = {
    "equity": "股市壓力", "xasset": "跨資產/流動性", "credit": "信用", "funding": "資金市場",
    "policy": "政策/利率", "growth": "增長", "internals": "市場內部", "ai": "AI 交易",
    "asia": "亞洲", "tw": "台股",
}

SCENARIOS = {
    "A": dict(name="去槓桿修正", analog="2018Q4 / 2024年8月", desc="股市恐慌但信用與資金市場平靜；通常數月內修復"),
    "B": dict(name="盈利下修熊市", analog="2000 科網", desc="AI 基本面轉弱 + 政策偏緊 + 增長放緩；多年熊市路徑"),
    "C": dict(name="信用事件", analog="2007 年中 / 2023 SVB", desc="壓力從股權擴散到債務人與放款人"),
    "D": dict(name="流動性危機", analog="2008/9、2020/3", desc="連美債都賣、美元急漲、資金市場失靈"),
}

SECTIONS = {"global": "全球", "us": "美國", "tw": "台股"}
