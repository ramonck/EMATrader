# RECONNECT · Refresh and recovery
- The app polls every five minutes on the clock and retries every two minutes when reads fail. It keeps running minimized. Sleep, shutdown or process exit interrupts monitoring.
- The cursor starts at activation. After reconnecting, the last closed directional turn after the cursor is eligible. Intermediate turns are skipped. Execution uses the price available then. Gray does not erase that turn.
- The vault records the market, candle, quantity, and last `trade_id` when a close starts. Each attempt records its `client_order_index` before submission. Recovery looks up that exact order and verifies the account's fills in the same market.
- Every two minutes, recovery can resume a pending close for the remaining original position using `reduce_only`. It waits while the order is active or unconfirmed. A change in history or position blocks submission. Lighter's direct lookup has a limited window for closed orders. If identity cannot be verified, check the position in Lighter.
- After restart, unlock the vault for the profile that had automation enabled. Recovery only closes the position linked to the journal. Re-enable automatic orders for new entries. In the terminal, use the same `--trade` and account arguments. **Monitor account only** disables desktop profile recovery.
- Code `Monitor.snapshot`, `take_signal` and `broker.execute`.
