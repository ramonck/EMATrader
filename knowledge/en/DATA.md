# DATA · Catalog, cache and journals
- The selector shows active Lighter perpetual symbols. Its disk catalog is valid for seven days. Each asset and interval has a short shared candle cache and local lock.
- `EMA_TRADER_DATA_DIR` overrides the root. Defaults: `%LOCALAPPDATA%/EMATrader` on Windows, `~/Library/Application Support/EMATrader` on macOS, and `$XDG_STATE_HOME/ema-trader` or `~/.local/state/ema-trader` on Linux.
- `profiles/`: desktop preferences. `quotes/`: candle cache. `history/`: last signal per asset. `Lighter/`: journals and locks by network and account. `operacoes-lighter.jsonl`: reconciled executions.
- The Lighter key comes from the session or environment. Preferences exclude it. Market feeds and monitoring use bounded windows. The OS manages swap.
- Code `storage.py`, `engine.markets`, `engine.shared_fetch` and `broker.main`.
