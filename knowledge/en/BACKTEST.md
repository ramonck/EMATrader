# BACKTEST · Lighter BTC perpetual · six months

- Sole source: Lighter Mainnet BTC perpetual, market 1, 15-minute candles. Local CSV `Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv` contains 18,720 contiguous bars. The test covers 2026-05-24 to 2026-11-24 at 03:00 UTC, with 17,664 bars and warm-up from May 13. Columns `open_time_ms,open,high,low,close,volume`. [Official candle API](https://github.com/elliottech/lighter-python/blob/main/docs/CandlestickApi.md)
- Reference scenario: $100 initial equity and base margin, 10× leverage, reinvestment, 0.05% fixed simulated cost per side, and account loss limit disabled. The model begins flat, fills at the next bar open, caps margin at available equity, and marks the remaining position at the end. ROI = marked ending equity ÷ initial equity − 1. Drawdown is measured at 15-minute closes. Funding, slippage, liquidation and minimum order sizes are outside the model.
- Same-data comparison: original rule −96.81% ROI, 99.51% max drawdown, 316 closed trades. v0.1.14 rule +454.91%, 82.04% max drawdown, 163 closed trades. From Aug 24 to Nov 24, starting flat with $100, ROI was −72.52% for the original rule and +135.80% for v0.1.14.
- The production rule requires a long trend on the last closed hourly bar and a raw 15-minute close above its open and upper band for a short-to-long turn. [SIGNALS](SIGNALS.md) · [Future change criteria](VERIFY.md)

```sh
python backtest.py Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv --input-minutes 15 --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --margin-usd 100 --leverage 10 --compound --fee-bps 5 --trend-confirm-short-exit
```

To reproduce the original rule, remove `--trend-confirm-short-exit`. For the validation window use `--start 2026-08-24T03:00:00Z` in both runs.
