# BACKTEST · BTC backtest · six months

- The local CSV contains Binance Spot BTCUSDT 5-minute candles with `open_time_ms,open,high,low,close,volume,close_time_ms`. The script aggregates three candles per 15-minute bar. Data before May 24 warms up the indicator. The test begins flat and executes each turn at the open after the signal close.
- Hypothetical fees apply to the notional of each entry and exit. The comparison uses 1× exposure and compounded equity. It excludes spread, slippage, funding, liquidation, latency and price differences between Binance Spot and Lighter perpetuals. This is a historical simulation.
- Drawdown is measured at 15-minute closes. At 0.01% per side, closed trades returned +24.12%, and buying and holding BTC returned −21.83% with the same fee. The remaining position was short. The two scenarios illustrate sensitivity to costs.

- With `--compound`, starting equity and base margin are $100 at 10×. A realized gain is added to the margin used. A loss resets the target to base. Entries are capped at available equity. ROI is ending marked equity divided by starting equity, minus one. Drawdown uses candle closes. The test assumes no top-ups and does not enforce Lighter's minimum order size.

- Without a drawdown trigger, 10× returned −51.25% and −96.52%, with drawdowns of 95.11% and 99.49% at 0.01% and 0.05% per side. With a 20%-of-margin per-trade stop at 10× and a 0.01% fee, ROI was −53.71% and drawdown 94.95%. The per-trade stop is a simulator option. The app uses the account drawdown trigger.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 1 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --stop-loss 20
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5 --margin-usd 100 --leverage 10 --compound

python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```

- Independent experiments: `--confirmation-bars 2`, `--require-market-close`, and `--trend-confirm-short-exit`. The last option only allows short→long if the last closed hourly trend is long and the 15-minute bar closes above both its open and its upper band. The app uses the original indicator reversal.
