# BACKTEST · Backtest de BTC · seis meses

- O CSV local contém candles BTCUSDT de 5 min da Binance Spot, com `open_time_ms,open,high,low,close,volume,close_time_ms`. O script agrega três candles por barra de 15 min. O trecho anterior a 24/05 aquece os indicadores. O período começa sem posição e executa cada virada na abertura seguinte ao fechamento do sinal.
- Custos hipotéticos sobre o valor nominal em cada entrada e saída. O cenário comparativo usa 1× e capital composto. Não modela spread, slippage, funding, liquidação, atraso nem a diferença de preço entre Binance Spot e os perpétuos da Lighter. Simulação histórica, sem extrapolação para operações reais.
- Queda máxima medida nos fechamentos de 15 min. A 0,01% por lado, operações já fechadas somaram +24,12% e comprar e manter BTC deu −21,83% com o mesmo custo. A posição que sobrou ficou em short. A diferença entre as duas linhas demonstra a sensibilidade ao custo.

- Com `--compound`, o saldo inicial e a margem base são US$ 100 a 10×. Após ganho realizado, soma-se o ganho à margem usada. Após perda, a meta volta à base. A entrada é limitada ao saldo disponível. O ROI é o saldo final marcado dividido pelo inicial, menos um. A queda máxima é medida nos fechamentos. O teste não injeta capital nem impõe o mínimo de ordem da Lighter.

- Sem trava, a 10×, o ROI foi −51,25% e −96,52%, com quedas de 95,11% e 99,49% a 0,01% e 0,05% por lado. Com stop individual de 20% da margem a 10× e custo de 0,01%, o ROI foi −53,71% e a queda 94,95%. O stop individual é uma opção do simulador. A trava da conta é a proteção usada no app.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 1 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --stop-loss 20
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5 --margin-usd 100 --leverage 10 --compound

python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```
Os filtros experimentais `--confirmation-bars 2` (dois candles consecutivos) e `--require-market-close` (fechamento real fora da faixa) estão disponíveis no simulador. O app usa a virada original do indicador.
