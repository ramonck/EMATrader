<p align="center"><img width="920" alt="EMA Trader" src="assets/banner.svg"></p>

<p align="center"><a href="README.md">Português</a> · <a href="README.en.md">English</a> · <a href="README.es.md">Español</a></p>

Monitor e execução opcional de perpétuos na Lighter com a faixa EMA Heikin Ashi de 15 minutos.

- **[Baixar](https://github.com/ramonck/EMATrader/releases/latest)** — A Release inclui Windows e macOS com janela e terminal, e Linux com terminal.
- **[Começar](knowledge/pt/ORDERS.md)** — Na janela use **Configurações → Idioma e MCP** para trocar o idioma. O terminal aceita `--lang pt|en|es`. Ao habilitar a automação, o app assume automaticamente a posição existente do ativo selecionado.
- **[Conectar por MCP](knowledge/pt/MCP.md)** — O MCP local permite consultar a instância em andamento, inclusive posição, P&L, sinal e regras.
- **[Base de conhecimento](knowledge/pt/index.md)** — O índice aponta para tópicos curtos que um novo chat pode consultar sem depender da conversa anterior.

Para gerar e publicar uma versão, abra **Actions → Compilar EMA Trader → Run workflow**. O próprio Action cria a tag e publica a Release com os cinco pacotes. [GitHub Actions](knowledge/pt/RELEASE.md)

## Rodar a partir do código

```sh
python -m pip install -r requirements.txt
python app.py --lang pt --symbol BTC
python app.py --lang pt --gui
python app.py --lang pt --subaccounts
python -m unittest -v
```

## Backtest de seis meses

BTC/USDT, Binance Spot, de 24/05/2026 a 24/11/2026 às 00h de Brasília. Faixa EMA de 15 minutos, exposição de 1× e reinvestimento do saldo. As duas linhas usam os mesmos candles locais.

| Custo por lado | ROI líquido | Queda máxima | Operações fechadas | Operações lucrativas |
| --- | ---: | ---: | ---: | ---: |
| 0,01% | **+26,63%** | 18,35% | 320 | 103 |
| 0,05% | **−2,03%** | 27,51% | 320 | 96 |

O ROI inclui a posição short que ficou aberta no fim, marcada pelo último fechamento. Compare os custos antes de tirar conclusões. [Reproduzir e conferir as premissas](knowledge/pt/BACKTEST.md)

## Conectar o MCP local

No EMA Trader, abra **Configurações → Idioma e MCP**, ative o MCP e copie o token. A porta padrão é `8765`. No terminal, defina `EMA_TRADER_MCP_TOKEN` com um token aleatório alfanumérico de pelo menos 24 caracteres antes de rodar `python app.py --mcp-port 8765`.

No Codex, adicione este bloco ao seu `~/.codex/config.toml` local e reinicie o cliente. Substitua `SEU_TOKEN` pelo token copiado. Guarde o arquivo fora do repositório.

```toml
[mcp_servers.ema_trader]
url = "http://127.0.0.1:8765/mcp"
http_headers = { Authorization = "Bearer SEU_TOKEN" }
```

No Claude Code, registre a URL e o mesmo token:

```sh
claude mcp add --transport http ema-trader http://127.0.0.1:8765/mcp --header "Authorization: Bearer SEU_TOKEN"
```

Com o app aberto, pergunte “Qual é a posição e o último sinal?” O MCP é opcional e só leitura. Para regras, peça o `knowledge_index` em `pt` e depois apenas o tópico necessário. [MCP](knowledge/pt/MCP.md)
