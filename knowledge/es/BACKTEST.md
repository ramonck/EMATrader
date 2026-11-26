# BACKTEST · Backtest de seis meses

- El CSV local contiene velas BTCUSDT de 5 min de Binance Spot con `open_time_ms,open,high,low,close,volume,close_time_ms`. El script agrega tres velas por barra de 15 min. Las anteriores al 24/05 sirven de calentamiento. La prueba empieza sin posición y ejecuta cada giro en la apertura siguiente al cierre de la señal.
- Costes hipotéticos sobre el nominal de cada entrada y salida. Usa 1× y capital compuesto. Omite spread, deslizamiento, financiación, liquidación, latencia y diferencias entre Binance Spot y perpetuos de Lighter. Es una simulación histórica.
- La caída máxima se mide en cierres de 15 min. Con 0,01% por lado, las operaciones cerradas dieron +24,12% y comprar y mantener BTC dio −21,83% con la misma comisión. La posición restante fue short. Los dos escenarios ilustran la sensibilidad al coste.

```sh
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 1
python backtest.py BTCUSDT-5m.csv --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --fee-bps 5
```
