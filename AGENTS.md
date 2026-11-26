# EMA Trader

For product behavior, open the knowledge index in the conversation language and load only the topics needed.

- [Português](knowledge/pt/index.md)
- [English](knowledge/en/index.md)
- [Español](knowledge/es/index.md)

Check referenced code and tests before changing behavior. Keep the same topic IDs and update affected topics in all three languages. Validate with `python -m unittest -v`. Use simulated data and mocked exchange calls in tests. The repository and its knowledge files are the handoff for a new chat.

Before accepting any trading logic change, replay the production baseline and candidate on the same local Lighter perpetual data with identical dates, costs, leverage, sizing, and risk settings. Require strictly higher ROI in the reference scenario and no ROI regression in a validation window reserved before testing. Record ROI, drawdown, trade count, and reproduction commands. Keep a candidate with equal, lower, or unverified reference ROI out of production. See [VERIFY](knowledge/en/VERIFY.md) and [BACKTEST](knowledge/en/BACKTEST.md). The public README reports only the current Lighter-only backtest result and its assumptions.
