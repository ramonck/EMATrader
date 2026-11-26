# SIGNALS · 15-minute EMA band
- Uses closed 15-minute candles from Lighter for every asset, including BTC. Candles come from the configured account network. With no configured account, the app monitors Mainnet. The calculation uses Heikin Ashi and a 21-period EMA of its highs and lows.
- After warm-up, compares both EMAs with their levels 22 candles earlier. Green requires the Heikin Ashi close above the upper EMA and both EMAs rising. Red requires a close below the lower EMA and both EMAs falling. All other cases are gray.
- The first green or red establishes direction. Gray holds the last direction. Repeating the active direction creates no order. The opposite color produces a reversal.
- **AL** opens long, **FL** closes long, **AS** opens short and **FS** closes short. Chart flags are theoretical signals. Real positions and P&L come from Lighter.
- Only 15 minutes drives execution. MFI, zones, Echo and AI reviews are not triggers in this version. Code `engine.ema_scalping`.
