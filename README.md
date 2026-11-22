# 市場壓力儀表板

每天兩次（上海時間 07:30、18:30）由 GitHub Actions 自動執行：

1. 抓數據：FRED（信用利差、利率、資金市場）、Yahoo Finance（股匯商品，備援 stooq）、證交所（融資、外資、跌停家數、融資維持率估算）
2. 計算 50+ 個指標的燈號、10 個層級的壓力、四個情境分數
3. 用真實歷史做回測：歷次回檔對照、條件式後續報酬、歷史類比
4. 產生 `docs/index.html`（GitHub Pages）並推送 Telegram 簡報

## 一次性設定
- Repo → Settings → Secrets and variables → Actions：
  - `TELEGRAM_BOT_TOKEN`（必要）
  - `FRED_API_KEY`（建議；沒有也能透過 FRED 公開 CSV 運作）
  - `TELEGRAM_CHAT_ID`（選填；沒有的話會自動抓最近傳訊息給 bot 的人）
- Repo → Settings → Pages → Source: Deploy from a branch → `main` / `/docs`

## 手動更新
- `state/manual.json`：hyperscaler capex 指引；宣布削減 capex 時把 `capex_cut_announced` 設為 `true`
- Actions → market-dashboard → Run workflow 可以隨時手動執行

## 本機測試
```
python -m tests.synthetic                       # 產生假資料
python -m pipeline.main --no-fetch --no-notify  # 不抓資料、不推送
```

## 檔案
- `pipeline/config.py` indicators, thresholds, scenarios (edit thresholds here)
- `pipeline/fetch.py` 數據抓取
- `pipeline/indicators.py` 指標與評分
- `pipeline/backtest.py` 回測與歷史類比
- `pipeline/render.py` 儀表板頁面
- `pipeline/telegram.py` Telegram 訊息

不是投資建議。
