# ORDERS · Real positions, adoption and execution
- Monitoring is the default. Orders require a subaccount key and explicit Mainnet enablement. On activation the app reads the selected market under the account lock and automatically adopts the full position and direction reported by Lighter, including manual positions. Activation itself sends no order and accepts future signals only.
- Active market orders, pending execution in its journal or a flat market with a mismatched journal block adoption. A position in another market prevents arming on a flat market and blocks new entries on that account.
- The first new turn against the position closes the real size with a `reduce_only` market order. A partial fill can trigger attempts to close the remainder. The app requires verified flat status before opening the other side and pauses if execution cannot be reconciled.
- Configured margin and leverage up to 20× apply to new positions, subject to the market cap. The order bound uses book depth. Insufficient liquidity can prevent a full close.
- Switching charts preserves the armed market. With a position there, the window returns on the next refresh after a five-minute browsing window. An optional beep marks a confirmed action.
- Code `Monitor.arm`, `broker.execute`, `broker.connect`. [RECONNECT](RECONNECT.md) · [DATA](DATA.md)
- Remove `--adopt-size` from older commands. The app now reads the position automatically for adoption.
