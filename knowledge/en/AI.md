# AI · Compact context for assistants
- EMA Trader serves data on demand over MCP. Reviews stay in the assistant you connect. MCP tools inspect positions, P&L, data age and summaries of the viewed and managed assets without querying the exchange.
- Start with `status`. It includes price, direction, EMA bounds, both EMA changes over 22 bars, range, price change and relative volume for up to 24 candles. UTC millisecond timestamps show data age.
- Call `candles` only for individual bars, with a limit of 1–24. For rules, use `knowledge_index` and `knowledge_rule` in the same language. Avoid loading the whole repository or all translations together.
