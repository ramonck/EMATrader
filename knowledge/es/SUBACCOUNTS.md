# SUBACCOUNTS · BTC y SOL en paralelo
1. En el selector de cuentas de Lighter, crea una subcuenta por estrategia.
2. Anota el índice y crea una clave vinculada a esa subcuenta. Asigna los saldos por separado.
3. Configura BTC en una subcuenta y SOL en la otra. Comprueba la red, el índice y el activo en Testnet antes de habilitar Mainnet.
4. Usa `--symbol BTC --account INDICE_BTC` y `--symbol SOL --account INDICE_SOL` en procesos de terminal separados. Define `LIGHTER_API_KEY` por separado en cada proceso.
Se puede compartir la caché pública. Registros y bloqueos se separan por red y cuenta. Para dos ventanas usa `--gui --profile BTC` y `--gui --profile SOL`. Usa puertos distintos si activas MCP en ambas.
