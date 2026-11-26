# SUBACCOUNTS · BTC e SOL em paralelo
1. Na Lighter, crie uma subconta por estratégia no seletor de conta.
2. Anote o índice e crie uma chave vinculada à subconta. Separe o saldo que cada uma vai usar.
3. Configure BTC em uma subconta e SOL na outra. Confira rede, índice e ativo em Testnet antes de habilitar Mainnet.
4. No terminal, use `--symbol BTC --account INDICE_BTC` e `--symbol SOL --account INDICE_SOL` em processos separados. Forneça `LIGHTER_API_KEY` separadamente em cada processo.
O cache público pode ser compartilhado. Diários e travas são separados por rede e conta. Para duas janelas, use `--gui --profile BTC` e `--gui --profile SOL`. Use portas distintas se ativar MCP em ambas.
