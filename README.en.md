<p align="center"><img width="920" alt="EMA Trader" src="assets/banner.svg"></p>

<p align="center"><a href="README.md">Português</a> · <a href="README.en.md">English</a> · <a href="README.es.md">Español</a></p>

Monitor perpetuals with a 15-minute Heikin Ashi EMA band. EMA Trader sources market data and executes orders exclusively through Lighter.

**Educational use.** This project provides no financial advice or recommendations about assets, platforms, or trades. When using real funds, continuously monitor the bot, orders, and positions. If something goes wrong, disable automation if possible and manage or close the position in the [official Lighter interface](https://app.lighter.xyz/). [Use and risk notice](DISCLAIMER.md#english)

## Why EMA Trader?

Elon Musk argues that advances in AI and robotics could make money irrelevant.

> There will still be constraints on power like electricity and mass. But I think at some point currency becomes irrelevant.
>
> — Elon Musk. [Business Insider](https://www.businessinsider.com/elon-musk-robotics-money-irrelevant-currency-universal-basic-income-2025-11)

EMA Trader applies automation to market monitoring and strategy execution with explicit rules.

- **[Download](https://github.com/ramonck/EMATrader/releases/latest)** — Releases include desktop and CLI packages for Windows and macOS, and CLI packages for Linux.
- **[Project website](https://ramonck.github.io/EMATrader/?lang=en)** — Overview, animated chart demo and Lighter backtest.
- **[Get started](knowledge/en/ORDERS.md)** — In the desktop app, use **Settings → Language and MCP**. The CLI accepts `--lang pt|en|es`. Enabling automation automatically adopts the selected asset's existing position.
- **[Connect via MCP](knowledge/en/MCP.md)** — Local MCP lets you inspect the running instance, including positions, P&L, signals and rules.
- **[Knowledge base](knowledge/en/index.md)** — The index points to short topics a new chat can read independently of prior conversation.

To build and publish a version, open **Actions → Compilar EMA Trader → Run workflow**. The Action creates the tag and publishes a Release with all five packages. [GitHub Actions](knowledge/en/RELEASE.md)

**Find an asset.** Type `BTC` or `NVDA` into **Find asset**. The list filters the Lighter catalog’s symbols. Press **Enter** to select the first result.


## Getting started with Lighter

Lighter is a protocol for trading perpetual futures in the Ethereum ecosystem. A perpetual tracks an asset price, such as BTC, without an expiry date. EMA Trader uses Lighter’s API to read account data and execute orders. Fees, spread and funding affect trading costs. Leveraged positions can be liquidated. [Lighter FAQ](https://lighter.xyz/faq) · [Official fee schedule](https://docs.lighter.xyz/trading/trading-fees)

Use the browser to connect your wallet and deposit. EMA Trader runs on your computer, calculates the EMA band and talks to the **Lighter API**. Its API key stays in the local vault. You can monitor the account before enabling orders.

```mermaid
flowchart LR
    subgraph LOCAL["Your computer"]
        B["Browser: app.lighter.xyz"]
        R["EMA Trader"]
        V["Local vault: API key"]
    end
    L["Lighter API and account"]
    M["Lighter market data: all assets"]
    B -->|"Connect wallet and deposit"| L
    V -->|"Key used to sign orders"| R
    M -->|"Public candles"| R
    R -->|"Send orders when enabled"| L
    L -->|"Position and P&L"| R
```

If Lighter is available to you, open **Deposit** before buying USDC. Note the asset, source network and minimum shown. Use the matching deposit route and check that the intended account receives the credit.

**Coinbase.** The guide covers ACH and how to send USDC to an eligible wallet or destination. Coinbase funding does not change the Lighter terms, which restrict its interface and API for U.S. residents and people located in the U.S. [Coinbase ACH](https://help.coinbase.com/en/exchange/funding/depositing-with-ach) · [Sending from Coinbase](https://help.coinbase.com/en-gb/coinbase/trading-and-funding/cryptocurrency-trading-pairs/steps-to-send-crypto) · [Lighter terms](https://lighter.xyz/terms)

[Full deposit and setup guide](knowledge/en/LIGHTER.md)

## Support the project

Enjoy EMA Trader and want to support the project? Send **native USDC** on **Arbitrum One** to this address:

```text
0x0FcbBFe9F4E39816799857E35887876B1d869929
```

Check the network and token in your wallet before sending.

## Security and verification

The local vault encrypts the Lighter key, account profile and private trading history. Open **Settings → Orders → Unlock vault**. Releases provide build attestations and SHA256 digests. [Vault and migration](knowledge/en/DATA.md) · [Verify a download](knowledge/en/RELEASE.md)


## Run from source

```sh
python -m pip install -r requirements.txt
python app.py --lang en --symbol BTC
python app.py --lang en --gui
python app.py --lang en --subaccounts
python -m unittest -v
```

## Lighter BTC perpetual backtest · six months

**Simulated ROI of +454.91%**, with 163 closed trades and an 82.04% maximum drawdown at 15-minute closes. The backtest uses only Lighter Mainnet BTC perpetual candles, from 2026-05-24 to 2026-11-24 at 03:00 UTC, with the v0.1.14 production rule.

The simulation uses $100 initial equity and base margin, 10× leverage, reinvestment and a fixed assumed cost of 0.05% per side. The account loss limit is disabled in this scenario. Execution uses candle opening prices. Funding, slippage and liquidation are outside the model. [Assumptions and reproduction](knowledge/en/BACKTEST.md)

## Connect to local MCP

In EMA Trader, open **Settings → Language and MCP**, enable MCP and copy the token. The default port is `8765`. For CLI set `EMA_TRADER_MCP_TOKEN` to a random alphanumeric token of at least 24 characters before running `python app.py --mcp-port 8765`.

In Codex, add this block to your local `~/.codex/config.toml` and restart the client. Replace `YOUR_TOKEN` with the copied token. Keep the file outside the repository.

```toml
[mcp_servers.ema_trader]
url = "http://127.0.0.1:8765/mcp"
http_headers = { Authorization = "Bearer YOUR_TOKEN" }
```

In Claude Code, register the URL and the same token:

```sh
claude mcp add --transport http ema-trader http://127.0.0.1:8765/mcp --header "Authorization: Bearer YOUR_TOKEN"
```

With the app running, ask “What is the current position and latest signal?” MCP is opt-in and read-only. For rules, request `knowledge_index` in `en` and then only the relevant topic. [MCP](knowledge/en/MCP.md)
