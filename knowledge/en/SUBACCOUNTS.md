# SUBACCOUNTS · Run BTC and SOL in parallel
1. In Lighter's account selector, create a subaccount for each strategy.
2. Note its account index and create an API key for that subaccount. Allocate each balance separately.
3. Configure BTC on one subaccount and SOL on the other. Verify network, index and asset on Testnet before enabling Mainnet.
4. Use `--symbol BTC --account BTC_INDEX` and `--symbol SOL --account SOL_INDEX` in separate CLI processes. Provide `LIGHTER_API_KEY` separately to each process.
The public cache can be shared. Journals and locks are scoped by network and account. For two windows use `--gui --profile BTC` and `--gui --profile SOL`. Use distinct ports if enabling MCP on both.
