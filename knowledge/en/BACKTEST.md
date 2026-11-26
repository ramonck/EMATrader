# BACKTEST · BTC backtest · six months

- The local CSV contains Binance Spot BTCUSDT 5-minute candles with `open_time_ms,open,high,low,close,volume,close_time_ms`. The script aggregates three candles per 15-minute bar. Data before May 24 warms up the indicator. The test begins flat and executes each turn at the open after the signal close.
- Hypothetical fees apply to the notional of each entry and exit. The comparison uses 1× exposure and compounded equity. It excludes spread, slippage, funding, liquidation, latency and price differences between Binance Spot and Lighter perpetuals. This is a historical simulation.
- Drawdown is measured at 15-minute closes. At 0.01% per side, closed trades returned +24.12%, and buying and holding BTC returned −21.83% with the same fee. The remaining position was short. The two scenarios illustrate sensitivity to costs.

- Fixed margin: the main scenario uses $100 per entry at 10× ($1,000 initial exposure), without reinvestment. Mean ROI is closed P&L divided by 320 trades and their per-order margin. Whole-account ROI depends on the initial account balance and available reserve.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5 --margin-usd 100 --leverage 10

python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```
