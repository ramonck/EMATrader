<p align="center"><img width="920" alt="EMA Trader" src="assets/banner.svg"></p>

<p align="center"><a href="README.md">Português</a> · <a href="README.en.md">English</a> · <a href="README.es.md">Español</a></p>

Monitor e execução opcional de perpétuos na Lighter com a faixa EMA Heikin Ashi de 15 minutos.

## Por que o EMA Trader?

Elon Musk acredita que a IA e a robótica podem tornar o dinheiro irrelevante.

> Ainda haverá limitações de energia, como a eletricidade, e de massa. Mas acho que, em algum momento, a moeda se torna irrelevante.
>
> — Elon Musk, em tradução livre. [Business Insider](https://www.businessinsider.com/elon-musk-robotics-money-irrelevant-currency-universal-basic-income-2025-11)

O EMA Trader aplica a automação ao monitoramento de mercado e à execução de estratégias com regras explícitas.

- **[Baixar](https://github.com/ramonck/EMATrader/releases/latest)** — A Release inclui Windows e macOS com janela e terminal, e Linux com terminal.
- **[Começar](knowledge/pt/ORDERS.md)** — Na janela use **Configurações → Idioma e MCP** para trocar o idioma. O terminal aceita `--lang pt|en|es`. Ao habilitar a automação, o app assume automaticamente a posição existente do ativo selecionado.
- **[Conectar por MCP](knowledge/pt/MCP.md)** — O MCP local permite consultar a instância em andamento, inclusive posição, P&L, sinal e regras.
- **[Base de conhecimento](knowledge/pt/index.md)** — O índice aponta para tópicos curtos que um novo chat pode consultar sem depender da conversa anterior.

Para gerar e publicar uma versão, abra **Actions → Compilar EMA Trader → Run workflow**. O próprio Action cria a tag e publica a Release com os cinco pacotes. [GitHub Actions](knowledge/pt/RELEASE.md)

**Busca de ativos.** Digite `BTC` ou `NVDA` no campo **Buscar ativo**. A lista filtra os códigos do catálogo da Lighter. Pressione **Enter** para selecionar o primeiro resultado.


## Segurança e verificação

O cofre local criptografa a chave da Lighter, o perfil da conta e o histórico privado. Abra **Configurações → Ordens → Desbloquear cofre**. As Releases trazem atestações de procedência e SHA256 dos pacotes. [Cofre e migração](knowledge/pt/DATA.md) · [Verificar download](knowledge/pt/RELEASE.md)


## Rodar a partir do código

```sh
python -m pip install -r requirements.txt
python app.py --lang pt --symbol BTC
python app.py --lang pt --gui
python app.py --lang pt --subaccounts
python -m unittest -v
```

## Backtest de BTC · seis meses

BTC/USDT da Binance Spot, de 24/05 a 24/11/2026 às 00h de Brasília. Faixa EMA de 15 minutos, **US$ 100 de saldo inicial e de margem base**. Após lucro, a próxima margem incorpora o ganho realizado. Após perda, a meta volta a US$ 100. Cada entrada usa até o saldo disponível, sem aportes na simulação.

| Custo por lado | Alavancagem | Saldo final | ROI da conta | Queda máxima | Operações fechadas |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,01% | 1× | US$ 127,00 | +27,00% | 17,88% | 320 |
| 0,01% | 10× | US$ 77,63 | −22,37% | 25,19% | 6 |
| 0,05% | 1× | US$ 82,82 | −17,18% | 25,05% | 284 |
| 0,05% | 10× | US$ 77,19 | −22,81% | 25,05% | 4 |

O teste usa uma trava de 25% sobre o pico do saldo. Ao atingir o limite no fechamento de 15 minutos, encerra a posição na abertura seguinte e pausa novas entradas. A queda pode ultrapassar o limite até o fechamento. Resultados sem trava e com stop individual estão nas [premissas e comandos](knowledge/pt/BACKTEST.md).

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
