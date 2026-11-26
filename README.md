<p align="center"><img width="920" alt="EMA Trader — Faixa EMA de 15 min" src="assets/banner.svg"></p>

<p align="center"><a href="#compilar-pelo-github">Compilar</a> · <a href="#rodar-a-partir-do-código">Executar</a> · <a href="#btc-e-sol-em-paralelo">Subcontas</a> · <a href="#dados-e-credenciais">Privacidade</a></p>

Monitor da faixa EMA Heikin Ashi de 15 minutos com execução opcional de perpétuos na Lighter.

| Faixa | Ação |
| --- | --- |
| 🟢 Verde | Long |
| 🔴 Vermelha | Short |
| ⚪ Cinza | Mantém a direção anterior |

| Plataforma | Janela | Terminal |
| --- | --- | --- |
| Windows x64 | Sim | Sim |
| macOS Apple Silicon e Intel | Sim | Sim |
| Linux x64 e ARM64 | — | Sim |

## Compilar pelo GitHub

Abra **Actions → Compilar EMA Trader → Run workflow**. Cada plataforma gera um pacote em **Artifacts**. O workflow não publica instaladores nem usa credenciais de corretora. Os pacotes macOS são builds de desenvolvimento e não incluem notarização da Apple.

## Rodar a partir do código

    python -m pip install -r requirements.txt
    python app.py --symbol BTC
    python app.py --gui
    python app.py --subaccounts
    python -m unittest -v

O modo padrão acompanha o mercado com ordens desligadas. Um índice de conta e uma rede permitem consultar posições abertas, inclusive manuais. No terminal, use também **--account** e **--network**. No modo gráfico, use **Configurações → Só acompanhar conta**.

Ordens pelo terminal exigem **--trade** e a variável de ambiente **LIGHTER_API_KEY**. Mainnet exige também **--confirm-mainnet**. Para assumir uma posição manual, informe sua quantidade exata com sinal em **--adopt-size**. Uma posição short tem quantidade negativa. A interface gráfica pede a quantidade antes da adoção.

## Monitoramento e reconexão

- O app usa candles fechados. Os sinais de BTC mantêm a fonte Binance Spot usada no backtest. Os demais ativos usam candles dos perpétuos Lighter.
- O catálogo fica em disco e é atualizado a cada sete dias. Cotações recentes também ficam em cache, com bloqueio para que instâncias locais compartilhem o mesmo resultado.
- Se a leitura falhar, o monitor tenta novamente em dois minutos. Após reconectar, processa a última virada direcional confirmada que perdeu enquanto estava aberto. A execução usa o preço disponível naquele momento. Resultados de ordem incertos ou posições divergentes pausam o envio.
- A janela pode ficar minimizada. Suspensão do computador, desligamento ou término do processo suspendem o monitoramento.
- A IA via OpenRouter usa dados de mercado e a faixa para revisão. Nenhuma posição é aberta por parecer da IA.

## BTC e SOL em paralelo

Use **Subcontas** no app ou **--subaccounts** no terminal. Configure uma subconta e uma chave próprias para cada execução. Instâncias no mesmo computador podem usar a mesma pasta de dados. O catálogo e as cotações são compartilhados, mas cada rede e conta têm seu próprio diário de ordens e trava de posição única.

Para abrir duas janelas com preferências separadas, execute **python app.py --gui --profile BTC** e **python app.py --gui --profile SOL** com Tk instalado, ou informe **--profile** diretamente ao executável gráfico. O executável de terminal distribuído foi compilado sem Tk. A janela padrão usa o perfil DEFAULT.

Se houver uma posição aberta em outro ativo na mesma conta, o robô bloqueia a próxima entrada. Numa virada, só envia a abertura após a Lighter confirmar que a posição anterior zerou. Uma execução incerta pode exigir conciliação manual do diário.

## Dados e credenciais

O app grava configurações sem segredos, catálogos, cotações e diários no diretório de dados do sistema. Para guardar tudo em uma pasta própria, defina **EMA_TRADER_DATA_DIR** como um caminho absoluto. Chaves ficam na sessão, nunca nos arquivos de dados. Para a IA, use **OPENROUTER_API_KEY** e opcionalmente **OPENROUTER_MODEL**.

Ao migrar de uma versão Windows anterior, o novo diário começa separado. Confira a posição real antes de assumi-la e mantenha apenas uma instância armada por conta durante a migração.

[Documentação da Lighter sobre tipos de conta e subcontas](https://docs.lighter.xyz/trading/trading-fees)
