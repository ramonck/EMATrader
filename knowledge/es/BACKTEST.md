# BACKTEST · Backtest de BTC · seis meses

- El CSV local contiene velas BTCUSDT de 5 min de Binance Spot con `open_time_ms,open,high,low,close,volume,close_time_ms`. El script agrega tres velas por barra de 15 min. Las anteriores al 24/05 sirven de calentamiento. La prueba empieza sin posición y ejecuta cada giro en la apertura siguiente al cierre de la señal.
- Costes hipotéticos sobre el nominal de cada entrada y salida. La comparación usa 1× y capital compuesto. Omite spread, deslizamiento, financiación, liquidación, latencia y diferencias entre Binance Spot y perpetuos de Lighter. Es una simulación histórica.
- La caída máxima se mide en cierres de 15 min. Con 0,01% por lado, las operaciones cerradas dieron +24,12% y comprar y mantener BTC dio −21,83% con la misma comisión. La posición restante fue short. Los dos escenarios ilustran la sensibilidad al coste.

- Con `--compound`, el saldo inicial y el margen base son US$ 100 a 10×. La ganancia realizada se suma al margen usado. Una pérdida restablece el objetivo al margen base. Cada entrada se limita al saldo disponible. El ROI es el saldo final valorado dividido por el inicial, menos uno. La caída máxima usa cierres. No se simulan aportes ni el tamaño mínimo de orden de Lighter.

- Sin límite de caída, a 10× el ROI fue −51,25% y −96,52%, con caídas de 95,11% y 99,49% al 0,01% y 0,05% por lado. Con un stop individual del 20% del margen a 10× y coste de 0,01%, el ROI fue −53,71% y la caída 94,95%. El stop individual es una opción del simulador. La aplicación usa el límite de caída de la cuenta.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 1 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --max-account-drawdown 25
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound --stop-loss 20
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1 --margin-usd 100 --leverage 10 --compound
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5 --margin-usd 100 --leverage 10 --compound

python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```
Los filtros experimentales `--confirmation-bars 2` (dos velas consecutivas) y `--require-market-close` (cierre real fuera de la banda) están disponibles en el simulador. La aplicación usa el giro original del indicador.
