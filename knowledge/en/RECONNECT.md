# RECONNECT · Refresh and recovery
- The app polls every five minutes on the clock and retries every two minutes when reads fail. It keeps running minimized. Sleep, shutdown or process exit interrupts monitoring.
- The cursor starts at activation. After reconnecting, the last closed directional turn after the cursor is eligible. Intermediate turns are skipped. Execution uses the price available then. Gray does not erase that turn.
- The journal records the candle and pending order before submission. If execution is uncertain, the app pauses automation for reconciliation. A new process starts in monitoring mode.
- Code `Monitor.snapshot`, `take_signal` and `broker.execute`.
