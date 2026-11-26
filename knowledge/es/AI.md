# AI · Contexto compacto para asistentes
- EMA Trader entrega datos bajo demanda por MCP. El análisis queda en el asistente conectado. MCP consulta posición, P&L, antigüedad y resúmenes de los activos visto y gestionado sin llamar a la bolsa.
- Empieza por `status`. Incluye precio, dirección, límites EMA, cambios de ambas EMA en 22 velas, rango, variación y volumen relativo de hasta 24 velas. Las horas UTC en milisegundos muestran la antigüedad.
- Pide `candles` solo para velas individuales, con un límite de 1 a 24. Para reglas usa `knowledge_index` y `knowledge_rule` en el mismo idioma. Evita cargar todo el repositorio o todas las traducciones a la vez.
