# LIGHTER · Lighter beginner guide

## Overview and costs

Lighter is a protocol for trading perpetual futures in the Ethereum ecosystem. A perpetual tracks an asset price, such as BTC, without an expiry date. EMA Trader uses Lighter’s API to read account data and execute orders. Fees, spread and funding affect trading costs. Leveraged positions can be liquidated. [Lighter FAQ](https://lighter.xyz/faq) · [Official fee schedule](https://docs.lighter.xyz/trading/trading-fees)

Public candles → 15-minute EMA band → signal → locally signed order → Lighter confirmation.

## Depositing on Lighter

USDC is a stablecoin designed to track the U.S. dollar. The network is the route your tokens travel on. An address starting with `0x` can exist on more than one network, so check the selected network as well. [USDC from Circle](https://www.circle.com/usdc)

1. Open [app.lighter.xyz](https://app.lighter.xyz/), check eligibility in the [Lighter terms](https://lighter.xyz/terms) and connect a wallet you control.
2. Open **Deposit** and choose USDC if offered. Read the available source networks and routing options. The screen tells you whether the route starts with your wallet, requires a transaction approval or gives you a deposit address.
3. Before buying or withdrawing, check the asset and network on both sides. For a route that starts in your wallet, withdraw to your own wallet address on the selected network. Then review and confirm the deposit in the official interface. If the screen provides a deposit address, follow the instructions for that route.
4. Arbitrum One has separate **native USDC** and **USDC.e** tokens. Check the one the route requires. If you sign a wallet transaction, check the network fee balance. Start with a small amount above the displayed minimum. [USDC networks and contracts](https://developers.circle.com/stablecoins/usdc-contract-addresses) · [Arbitrum One](https://docs.arbitrum.io/arbitrum-bridge/quickstart)
5. Confirm the deposit in Lighter’s deposit history and check your trading account balance. A wallet balance shows an exchange withdrawal reached your wallet. Lighter credits the account after the platform deposit.

## Buying USDC by bank transfer

- **United States and ACH.** ACH moves U.S. dollars between bank accounts and an eligible U.S. exchange. Coinbase Exchange, for example, documents linking a verified bank account, choosing USD and requesting a bank deposit. You can then buy USDC if available. An exchange can hold withdrawals until the deposit clears. Lighter’s terms restrict its interface and API for U.S. residents and people located in the U.S. This example describes ACH funding at the exchange. [Coinbase ACH](https://help.coinbase.com/en/exchange/funding/depositing-with-ach) · [Lighter terms](https://lighter.xyz/terms)
- **Where Lighter is available.** Use a provider serving your jurisdiction, credit local currency by bank transfer and buy USDC. Check whether the provider can send the required USDC token on a network offered by the Lighter deposit screen. Review the withdrawal fee and net amount before sending.

## Connecting EMA Trader

1. On the Lighter account or subaccount you want to monitor, note the **account index** and generate an API key linked to it. Note the **key index** too. The account index identifies the account and the key index identifies the credential.
2. In EMA Trader, open **Settings → Orders** and unlock the vault. Select **Mainnet** for the live account. Enter its account index and choose **Monitor account only** to check the position. Check the available balance in the Lighter interface.
3. To test orders with test funds, use Testnet and create a key for that network. To enable orders, enter the API private key, base margin and leverage in the app. Keep your wallet recovery phrase outside the app.
4. Keep EMA Trader running to monitor and execute signals. You can close the browser after account setup.

[Open Testnet](https://testnet.app.lighter.xyz/) · [ORDERS](ORDERS.md) · [SUBACCOUNTS](SUBACCOUNTS.md) · [DATA](DATA.md)
