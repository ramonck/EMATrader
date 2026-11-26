# BACKTEST · Backtest de seis meses

- O CSV local contém candles BTCUSDT de 5 min da Binance Spot, com `open_time_ms,open,high,low,close,volume,close_time_ms`. O script agrega três candles por barra de 15 min. O trecho anterior a 24/05 aquece os indicadores. O período começa sem posição e executa cada virada na abertura seguinte ao fechamento do sinal.
- Custos hipotéticos sobre o valor nominal em cada entrada e saída. Usa 1× e capital composto. Não modela spread, slippage, funding, liquidação, atraso nem a diferença de preço entre Binance Spot e os perpétuos da Lighter. Simulação histórica, sem extrapolação para operações reais.
- Queda máxima medida nos fechamentos de 15 min. A 0,01% por lado, operações já fechadas somaram +24,12% e comprar e manter BTC deu −21,83% com o mesmo custo. A posição que sobrou ficou em short. A diferença entre as duas linhas demonstra a sensibilidade ao custo.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```
