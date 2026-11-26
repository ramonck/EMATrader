# BACKTEST · BTC perpétuo na Lighter · seis meses

- Fonte exclusiva: BTC perpétuo da Lighter Mainnet, mercado 1, candles de 15 min. O CSV local `Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv` contém 18.720 barras contínuas. O teste cobre 24/05/2026 a 24/11/2026 às 03:00 UTC, com 17.664 barras e aquecimento desde 13/05. Colunas `open_time_ms,open,high,low,close,volume`. [API oficial de candles](https://github.com/elliottech/lighter-python/blob/main/docs/CandlestickApi.md)
- Cenário de referência: US$ 100 de saldo inicial e margem base, 10×, reinvestimento, custo simulado de 0,05% por lado e trava de perda desativada. O modelo começa zerado, executa na abertura seguinte, limita a margem ao patrimônio disponível e marca a posição restante no fim. ROI = saldo final marcado ÷ saldo inicial − 1. Drawdown medido nos fechamentos de 15 min. Funding, slippage, liquidação e tamanho mínimo de ordem ficam fora do modelo.
- Comparação no mesmo arquivo: regra original −96,81% de ROI, 99,51% de drawdown, 316 operações fechadas. Regra v0.1.14 +454,91%, 82,04% de drawdown, 163 operações fechadas. Na janela de 24/08 a 24/11, reiniciando zerado com US$ 100, o ROI foi −72,52% na referência original e +135,80% na v0.1.14.
- A regra de produção exige tendência long na última barra de 1h fechada e fechamento real de 15 min acima da abertura e da faixa superior para virar de short para long. [SIGNALS](SIGNALS.md) · [Critério para mudanças futuras](VERIFY.md)

```sh
python backtest.py Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv --input-minutes 15 --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --margin-usd 100 --leverage 10 --compound --fee-bps 5 --trend-confirm-short-exit
```

Para reproduzir a referência original, retire `--trend-confirm-short-exit`. Para reproduzir a janela de validação, use `--start 2026-08-24T03:00:00Z` em ambos.
