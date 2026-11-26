# SIGNALS · Banda EMA de 15 min
- Usa velas cerradas de 15 minutos de Lighter para todos los activos, incluido BTC. Las velas provienen de la red de la cuenta configurada. Si no hay cuenta configurada, la aplicación sigue Mainnet. El cálculo usa Heikin Ashi y EMA 21 de sus máximos y mínimos.
- Tras el calentamiento, compara ambas EMA con sus valores de 22 velas atrás. Verde requiere cierre Heikin Ashi sobre la EMA superior y subida de ambas EMA. Rojo requiere cierre bajo la EMA inferior y caída de ambas. Los demás casos son grises.
- El primer verde o rojo establece la dirección. Gris mantiene la última dirección. Repetir el color de la dirección actual no genera orden. El color contrario genera el giro.
- **AL** abre long, **FL** cierra long, **AS** abre short y **FS** cierra short. Las marcas del gráfico son señales teóricas. La posición y el P&L reales provienen de Lighter.
- Solo 15 minutos dirige la ejecución. MFI, zonas, Echo y el análisis de IA no son disparadores en esta versión. Código `engine.ema_scalping`.
