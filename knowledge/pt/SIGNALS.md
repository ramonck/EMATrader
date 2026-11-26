# SIGNALS · Faixa EMA de 15 min
- Usa candles fechados de 15 minutos da Lighter para todos os ativos, inclusive BTC. Os candles vêm da rede da conta configurada. Quando nenhuma conta está configurada, o app acompanha a Mainnet. O cálculo usa Heikin Ashi e EMA 21 das máximas e mínimas.
- Após o aquecimento, compara as duas EMAs com seus valores de 22 candles atrás. Verde exige fechamento Heikin Ashi acima da EMA superior e alta nas duas EMAs. Vermelho exige fechamento abaixo da EMA inferior e queda nas duas. O restante é cinza.
- O primeiro verde ou vermelho estabelece a direção. Cinza mantém a última direção. Repetir a cor da direção atual não gera uma ordem. A cor oposta gera a virada.
- **AL** abre long, **FL** fecha long, **AS** abre short, **FS** fecha short. No gráfico são sinais teóricos. A posição e o P&L reais vêm da conta Lighter.
- Execução usa apenas 15 min. MFI, zonas, Echo e parecer da IA não são gatilhos nesta versão. Código `engine.ema_scalping`.
