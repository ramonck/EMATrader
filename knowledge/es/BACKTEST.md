# BACKTEST · BTC perpetuo en Lighter · seis meses

- Fuente exclusiva: BTC perpetuo de Lighter Mainnet, mercado 1, velas de 15 min. El CSV local `Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv` contiene 18.720 velas continuas. El periodo va del 24/05/2026 al 24/11/2026 a las 03:00 UTC, con 17.664 velas y calentamiento desde el 13/05. Columnas `open_time_ms,open,high,low,close,volume`. [API oficial de velas](https://github.com/elliottech/lighter-python/blob/main/docs/CandlestickApi.md)
- Escenario de referencia: US$ 100 de saldo inicial y margen base, 10×, reinversión, coste simulado fijo del 0,05% por lado y límite de pérdida desactivado. El modelo empieza sin posición, ejecuta en la apertura siguiente, limita el margen al patrimonio disponible y valora la posición restante al final. ROI = patrimonio final valorado ÷ patrimonio inicial − 1. La caída se mide en los cierres de 15 min. Funding, deslizamiento, liquidación y tamaño mínimo de orden quedan fuera del modelo.
- Comparación con el mismo archivo: regla original −96,81% de ROI, caída máxima del 99,51% y 316 operaciones cerradas. Regla v0.1.14 +454,91%, caída máxima del 82,04% y 163 operaciones cerradas. Del 24/08 al 24/11, empezando sin posición y con US$ 100, el ROI fue −72,52% con la regla original y +135,80% en la v0.1.14.
- La regla de producción exige tendencia long en la última vela cerrada de 1 h y cierre real de 15 min por encima de su apertura y de la banda superior para girar de short a long. [SIGNALS](SIGNALS.md) · [Criterio de cambios futuros](VERIFY.md)

```sh
python backtest.py Lighter-BTC-PERP-15m-20260513T0300Z--20261124T0300Z.csv --input-minutes 15 --start 2026-05-24T03:00:00Z --end 2026-11-24T03:00:00Z --margin-usd 100 --leverage 10 --compound --fee-bps 5 --trend-confirm-short-exit
```

Para reproducir la referencia original, quita `--trend-confirm-short-exit`. Para la ventana de validación usa `--start 2026-08-24T03:00:00Z` en ambas ejecuciones.
