# DATA · Catálogo, cache e diários
- Na janela, digite um código como BTC ou NVDA em **Buscar ativo** para filtrar o catálogo. A correspondência exata vem primeiro. **Enter** seleciona o primeiro resultado sem trocar o ativo armado.
- `Lighter/risk/` guarda o pico do saldo e a pausa da trava de perda por rede e conta. O diário do mercado guarda a referência do saldo e a margem de reinvestimento. [ORDERS](ORDERS.md)
- A lista expõe os símbolos dos perpétuos ativos da Lighter. Catálogo em disco com validade de sete dias. Candles por ativo e intervalo têm cache curto compartilhado e trava local.
- `EMA_TRADER_DATA_DIR` define a raiz. Por padrão: `%LOCALAPPDATA%/EMATrader` no Windows, `~/Library/Application Support/EMATrader` no macOS e `$XDG_STATE_HOME/ema-trader` ou `~/.local/state/ema-trader` no Linux.
- `profiles/`: preferências gráficas por perfil. `quotes/`: cache de candles. `history/`: último sinal por ativo. `Lighter/`: diários e travas por rede e conta. `operacoes-lighter.jsonl`: execuções conciliadas.
- A chave da Lighter vem da sessão ou do ambiente. Não fica nas preferências. O feed e o monitor mantêm janelas limitadas. O sistema operacional gerencia swap.
- Código `storage.py`, `engine.markets`, `engine.shared_fetch` e `broker.main`.
