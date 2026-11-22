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
    "BBB_OAS": "BAMLC0A4CBBB",   # ICE BofA BBB OAS (Oracle's rating bucket)
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
    # ---- AI funding chain module
    "NBIS": "NBIS", "ANT": "ANT", "AVGO": "AVGO", "TSM": "TSM", "MU": "MU",
    "SKHYNIX": "000660.KS", "SAMSUNG": "005930.KS",
    "HONHAI": "2317.TW", "QUANTA": "2382.TW", "WIWYNN": "6669.TW", "WISTRON": "3231.TW",
    "GEV": "GEV", "VRT": "VRT", "OWL": "OWL", "SMH": "SMH",
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

# AI funding chain: risk travels left -> right (weakest balance sheet first)
NEOCLOUD = ["CRWV", "NBIS"]
HYPERSCALERS = ["MSFT", "GOOGL", "AMZN", "META"]
UPSTREAM = ["NVDA", "AVGO", "TSM", "MU", "SKHYNIX", "SAMSUNG"]
TW_CHAIN = ["TSMC", "HONHAI", "QUANTA", "WIWYNN", "WISTRON"]
POWER = ["GEV", "VRT"]
ANT_IPO_PRICE = 83.0
# (name, members, 20-day return that counts as "this link has cracked", %)
CHAIN_LINKS = [
    ("Neocloud", NEOCLOUD, -15.0),
    ("Oracle", ["ORCL"], -10.0),
    ("Nvidia / memory", ["NVDA", "MU", "SKHYNIX"], -8.0),
    ("Hyperscalers", HYPERSCALERS, -6.0),
]

# ---------------------------------------------------------------- indicators
# dir  +1: higher = more stress, -1: lower = more stress
# mode "abs": amber/red are absolute levels; "pct": amber/red are history percentiles
# fmt: python format for display; unit shown after value
IND = [
    # ---- global / cross-asset
    dict(id="acwi_dd", sec="global", grp="equity", name="Global equities drawdown (ACWI)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20,
         note="Decline from 52-week high"),
    dict(id="everything_down", sec="global", grp="xasset", name="Stocks/bonds/gold down together (10d)", unit="d", fmt="{:.0f}", dir=1, mode="abs", amber=1, red=3,
         note="Days SPY fell >1% while TLT and gold also fell; detects 2020-style 'sell everything'"),
    dict(id="stock_bond_corr", sec="global", grp="xasset", name="Stock-bond correlation (20d)", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=0.3, red=0.6,
         note="SPY vs TLT returns; positive = bonds no longer hedge"),
    dict(id="dollar_1m", sec="global", grp="xasset", name="US dollar, 1M change", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97,
         note="A dollar spike = global dollar shortage"),
    dict(id="usdjpy_1m", sec="global", grp="xasset", name="Yen carry stress (USDJPY 1M)", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.15, red=0.04,
         note="Sharp yen rally = carry-trade unwind (Aug 2024 style)"),
    dict(id="gold_1m", sec="global", grp="xasset", name="Gold, 1M return", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.10, red=0.03,
         note="Haven assets being sold = deleveraging / margin calls"),
    dict(id="btc_dd", sec="global", grp="equity", name="Bitcoin drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-25, red=-45,
         note="Leverage and risk-appetite thermometer"),
    dict(id="copper_gold", sec="global", grp="growth", name="Copper/gold ratio, 3M change", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.15, red=0.05,
         note="Falling = market pricing slower growth"),
    dict(id="kospi_dd", sec="global", grp="asia", name="Korea drawdown (KOSPI)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note="Core of the AI trade in Asia"),
    dict(id="n225_dd", sec="global", grp="asia", name="Japan drawdown (Nikkei)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="hsi_dd", sec="global", grp="asia", name="Hong Kong drawdown (Hang Seng)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="cny_1m", sec="global", grp="asia", name="Yuan, 1M change (USDCNY)", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97, note="Positive = yuan weakening"),

    # ---- US: credit
    dict(id="hy_oas", sec="us", grp="credit", name="High-yield spread (HY OAS)", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=4.0, red=5.0,
         note="Peaks: 2018Q4 ~5.3%, Mar 2020 ~10.9%, 2008 ~19.9%"),
    dict(id="hy_oas_chg", sec="us", grp="credit", name="HY spread, 1M change", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=50, red=120, note="Speed matters more than level"),
    dict(id="ig_oas", sec="us", grp="credit", name="Investment-grade spread (IG OAS)", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=1.3, red=1.7,
         note="Most AI infrastructure debt is IG (Oracle, hyperscalers)"),
    dict(id="ccc_oas", sec="us", grp="credit", name="CCC spread", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=9.0, red=12.0, note="Weakest borrowers"),
    dict(id="baa10y", sec="us", grp="credit", name="Baa corporate spread (long history)", unit="%", fmt="{:.2f}", dir=1, mode="pct", amber=0.80, red=0.95,
         note="Moody's Baa − 10Y since 1986; used for backtests"),
    dict(id="hyg_lqd_1m", sec="us", grp="credit", name="HYG/LQD, 1M change", unit="%", fmt="{:+.1f}", dir=-1, mode="pct", amber=0.10, red=0.03, note="Junk vs investment grade"),
    dict(id="bizd_dd", sec="us", grp="credit", name="BDC drawdown (private credit proxy)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20,
         note="Private credit marks quarterly; BDC prices move first"),
    dict(id="kre_dd", sec="us", grp="credit", name="Regional banks drawdown (KRE)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-25, note="2023 SVB-style signal"),

    # ---- US: funding
    dict(id="sofr_iorb", sec="us", grp="funding", name="SOFR − IORB", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=0, red=10,
         note="Positive = repo market short of cash (Sep 2019 style)"),
    dict(id="srf", sec="us", grp="funding", name="Fed standing repo usage", unit="$bn", fmt="{:.1f}", dir=1, mode="abs", amber=1, red=10, note=">0 = someone borrowing emergency cash from the Fed"),
    dict(id="stlfsi", sec="us", grp="funding", name="St. Louis Fed Financial Stress", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=0, red=1.5, note="0 = historical average (weekly)"),
    dict(id="nfci", sec="us", grp="funding", name="Chicago Fed NFCI", unit="", fmt="{:+.2f}", dir=1, mode="abs", amber=-0.2, red=0.2, note=">0 = tighter than average (weekly)"),
    dict(id="move", sec="us", grp="funding", name="Treasury volatility (MOVE)", unit="", fmt="{:.0f}", dir=1, mode="abs", amber=110, red=140, note="Bond-market liquidity stress"),

    # ---- US: vol
    dict(id="vix", sec="us", grp="equity", name="VIX", unit="", fmt="{:.1f}", dir=1, mode="abs", amber=25, red=35, note=""),
    dict(id="vix_term", sec="us", grp="equity", name="VIX term structure (VIX/VIX3M)", unit="", fmt="{:.2f}", dir=1, mode="abs", amber=1.0, red=1.1,
         note=">1 inverted = acute panic; back below 0.9 = panic fading"),

    # ---- US: policy / rates
    dict(id="fed_path", sec="us", grp="policy", name="Hikes priced (2Y − Fed funds)", unit="bp", fmt="{:+.0f}", dir=1, mode="abs", amber=25, red=60,
         note="Positive = market expects more hikes"),
    dict(id="real10", sec="us", grp="policy", name="10Y real yield", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=2.0, red=2.5, note="High real yields compress valuations"),
    dict(id="dgs10", sec="us", grp="policy", name="10Y Treasury yield", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=4.75, red=5.25, note=""),
    dict(id="breakeven", sec="us", grp="policy", name="5Y inflation breakeven", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=2.7, red=3.1, note="How boxed-in the Fed is"),
    dict(id="curve", sec="us", grp="growth", name="Yield curve (10Y − 3M)", unit="bp", fmt="{:+.0f}", dir=-1, mode="abs", amber=0, red=-75, note="Inversion = recession signal"),
    dict(id="claims", sec="us", grp="growth", name="Initial jobless claims (4wk avg)", unit="k", fmt="{:.0f}", dir=1, mode="abs", amber=260, red=300, note=""),

    # ---- US: internals / AI
    dict(id="spx_dd", sec="us", grp="equity", name="S&P 500 drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="ndx_dd", sec="us", grp="equity", name="Nasdaq 100 drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="sectors_200", sec="us", grp="internals", name="Sectors above 200-day MA", unit="/11", fmt="{:.0f}", dir=-1, mode="abs", amber=6, red=3, note="Market breadth"),
    dict(id="rsp_spy_3m", sec="us", grp="internals", name="Equal vs cap weight (3M)", unit="%", fmt="{:+.1f}", dir=1, mode="abs", amber=4, red=8,
         note="Large positive = mega-caps sold, money leaving AI leaders"),
    dict(id="sox_dd", sec="us", grp="ai", name="Semiconductors drawdown (SOX)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-20, red=-35, note=""),
    dict(id="ai_dd", sec="us", grp="ai", name="AI leaders basket drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30,
         note="NVDA, MSFT, META, GOOGL, AMZN, ORCL"),

    # ---- AI funding chain: credit (the alarm)
    dict(id="bbb_oas", sec="ai", grp="aicredit", name="BBB spread", unit="%", fmt="{:.2f}", dir=1, mode="abs", amber=1.5, red=2.0,
         note="Oracle's rating bucket (BBB-); hyperscaler borrowing cost"),
    dict(id="credit_eq_div", sec="ai", grp="aicredit", name="Credit-equity divergence days (10d)", unit="d", fmt="{:.0f}", dir=1, mode="abs", amber=1, red=4,
         note="HYG down over 20d while neoclouds rally; in these divergences credit is usually right"),
    dict(id="bizd_hyg_1m", sec="ai", grp="aicredit", name="Private credit vs high yield (1M)", unit="%", fmt="{:+.1f}", dir=-1, mode="abs", amber=-3, red=-6,
         note="BDC ETF relative to HYG; negative = more stress in private credit than public"),
    dict(id="owl_dd", sec="ai", grp="aicredit", name="Blue Owl drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-25, red=-45,
         note="Major private lender to data centers"),
    # ---- AI funding chain: transmission
    dict(id="ai_chain_stage", sec="ai", grp="aichain", name="Contagion stage", unit="/4", fmt="{:.0f}", dir=1, mode="abs", amber=2, red=3,
         note="Neocloud → Oracle → Nvidia/memory → hyperscalers: links cracked in order"),
    dict(id="neocloud_dd", sec="ai", grp="aichain", name="Neocloud drawdown (CRWV, NBIS)", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-30, red=-50,
         note="Weakest link"),
    dict(id="orcl_dd", sec="ai", grp="aichain", name="Oracle drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-30, red=-50, note="Poster child for debt-funded AI build-out"),
    dict(id="crwv_dd", sec="ai", grp="aichain", name="CoreWeave drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-40, red=-65, note="AI compute rental + high leverage"),
    dict(id="upstream_dd", sec="ai", grp="aichain", name="Upstream basket drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30,
         note="NVDA, AVGO, TSM, MU, SK Hynix, Samsung"),
    dict(id="hyper_dd", sec="ai", grp="aichain", name="Hyperscaler basket drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20,
         note="MSFT, GOOGL, AMZN, META (most cash, should fall last)"),
    dict(id="tw_chain_dd", sec="ai", grp="aichain", name="Taiwan AI supply chain drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30,
         note="TSMC, Hon Hai, Quanta, Wiwynn, Wistron"),
    dict(id="power_dd", sec="ai", grp="aichain", name="Power bottleneck stocks drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-20, red=-35, note="GEV, VRT"),
    dict(id="ant_vs_ipo", sec="ai", grp="aichain", name="Anthropic vs IPO price", unit="%", fmt="{:+.1f}", dir=-1, mode="abs", amber=0, red=-20,
         note="IPO at $83; trading below = weaker primary-market appetite"),
    dict(id="up_vs_hyper", sec="ai", grp="airegime", name="Upstream ÷ hyperscalers (3M change)", unit="%", fmt="{:+.1f}", dir=1, mode="info", amber=None, red=None,
         note="Rising = market betting capex keeps growing; falling = betting capex peaks and hyperscaler cash flow recovers"),

    # ---- Taiwan
    dict(id="twii_dd", sec="tw", grp="tw", name="TAIEX drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-10, red=-20, note=""),
    dict(id="twoii_dd", sec="tw", grp="tw", name="Taipei OTC index drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-12, red=-25, note=""),
    dict(id="tsmc_dd", sec="tw", grp="tw", name="TSMC drawdown", unit="%", fmt="{:.1f}", dir=-1, mode="abs", amber=-15, red=-30, note=""),
    dict(id="tw_margin", sec="tw", grp="tw", name="TWSE margin loans outstanding", unit="NT$bn", fmt="{:,.1f}", dir=1, mode="pct", amber=0.85, red=0.97, note="Leverage level"),
    dict(id="tw_margin_5d", sec="tw", grp="tw", name="Margin loans, 5-day change", unit="%", fmt="{:+.1f}", dir=-1, mode="abs", amber=-5, red=-10, note="Rapid fall = forced-liquidation wave"),
    dict(id="tw_delever", sec="tw", grp="tw", name="Deleveraging progress (margin fall ÷ index fall)", unit="x", fmt="{:.2f}", dir=-1, mode="abs", amber=0.8, red=0.5,
         note="From the index peak; >1 = margin cut faster than the index (tested on the Backtest tab)"),
    dict(id="tw_maint", sec="tw", grp="tw", name="TWSE margin maintenance ratio (est.)", unit="%", fmt="{:.0f}", dir=-1, mode="abs", amber=160, red=145,
         note="Margin holdings value ÷ margin loans; 130% triggers margin calls"),
    dict(id="tw_foreign_5d", sec="tw", grp="tw", name="Foreign investors net buy, 5d", unit="NT$bn", fmt="{:+,.1f}", dir=-1, mode="pct", amber=0.10, red=0.03, note=""),
    dict(id="tw_limitdown", sec="tw", grp="tw", name="TWSE limit-down count", unit="", fmt="{:.0f}", dir=1, mode="abs", amber=40, red=120, note="Stocks locked limit-down = market liquidity drying up"),
    dict(id="twd_1m", sec="tw", grp="tw", name="Taiwan dollar, 1M change (USDTWD)", unit="%", fmt="{:+.1f}", dir=1, mode="pct", amber=0.85, red=0.97, note="Positive = TWD weakening, capital outflow"),
]
IND_BY_ID = {d["id"]: d for d in IND}

GROUP_NAMES = {
    "equity": "Equity stress", "xasset": "Cross-asset / liquidity", "credit": "Credit", "funding": "Funding markets",
    "policy": "Policy / rates", "growth": "Growth", "internals": "Market internals", "ai": "AI trade",
    "asia": "Asia", "tw": "Taiwan",
    "aicredit": "AI credit (the alarm)", "aichain": "AI contagion chain", "airegime": "Where money is betting",
}

SCENARIOS = {
    "A": dict(name="Deleveraging correction", analog="2018Q4 / Aug 2024", desc="Equity panic while credit and funding stay calm; usually repaired within months"),
    "B": dict(name="Earnings-downgrade bear market", analog="2000 dot-com", desc="AI fundamentals weaken + tight policy + slowing growth; multi-year bear path"),
    "C": dict(name="Credit event", analog="mid-2007 / 2023 SVB", desc="Stress spreads from equity to borrowers and lenders"),
    "D": dict(name="Liquidity crisis", analog="Sep 2008 / Mar 2020", desc="Even Treasuries sold, dollar spikes, funding markets break"),
}

SECTIONS = {"global": "Global", "us": "US", "ai": "AI funding chain", "tw": "Taiwan"}
