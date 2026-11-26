# DATA · Catálogo, caché y registros
- El selector muestra símbolos perpetuos activos de Lighter. El catálogo en disco dura siete días. Cada activo e intervalo tiene una caché breve compartida y un bloqueo local.
- `EMA_TRADER_DATA_DIR` cambia la raíz. Predeterminados: `%LOCALAPPDATA%/EMATrader` en Windows, `~/Library/Application Support/EMATrader` en macOS y `$XDG_STATE_HOME/ema-trader` o `~/.local/state/ema-trader` en Linux.
- `profiles/`: preferencias de la ventana. `quotes/`: caché de velas. `history/`: última señal por activo. `Lighter/`: registros y bloqueos por red y cuenta. `operacoes-lighter.jsonl`: ejecuciones conciliadas.
- La clave de Lighter proviene de la sesión o del entorno. Se excluye de las preferencias. Los datos y el monitor usan ventanas limitadas. El sistema operativo gestiona swap.
- Código `storage.py`, `engine.markets`, `engine.shared_fetch` y `broker.main`.
