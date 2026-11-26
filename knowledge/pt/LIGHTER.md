# LIGHTER · Lighter para iniciantes

## Visão geral e custos

A Lighter é um protocolo de negociação de contratos perpétuos no ecossistema Ethereum. Um perpétuo acompanha o preço de um ativo, como BTC, sem data de vencimento. O EMA Trader usa a Lighter porque ela oferece uma API para consultar a conta e executar ordens. Taxas, spread e funding podem afetar o resultado. Com alavancagem, uma posição pode ser liquidada. [FAQ da Lighter](https://lighter.xyz/faq) · [Tabela oficial de taxas](https://docs.lighter.xyz/trading/trading-fees)

Candles públicos → faixa EMA de 15 minutos → sinal → ordem assinada localmente → confirmação da Lighter.

## Depositar na Lighter

USDC é uma stablecoin que busca acompanhar o dólar americano. A rede é o caminho por onde o token será transferido. Um endereço que começa com `0x` pode aparecer em mais de uma rede, então confira também a rede selecionada. [USDC na Circle](https://www.circle.com/usdc)

1. Acesse [app.lighter.xyz](https://app.lighter.xyz/), confira a elegibilidade nos [termos da Lighter](https://lighter.xyz/terms) e conecte uma carteira sua.
2. Abra **Depositar** e selecione USDC, quando disponível. Veja quais redes e rotas são oferecidas para a sua conta. A tela informa se você precisa usar sua carteira, aprovar uma transação ou enviar para um endereço de depósito gerado.
3. Antes de comprar ou sacar, confirme a rede e o token nas duas pontas. Se a rota começa na sua carteira, saque da corretora para o endereço da sua própria carteira na rede escolhida. Depois revise e confirme o depósito na interface oficial. Se a tela oferecer um endereço de depósito, siga as instruções exibidas para aquela rota.
4. Na Arbitrum One, **USDC nativo** e **USDC.e** são tokens diferentes. Confira o que a rota pede. Se for assinar uma transação na carteira, verifique o saldo para a taxa de rede. Faça primeiro um envio pequeno que supere o mínimo indicado. [Redes e contratos de USDC](https://developers.circle.com/stablecoins/usdc-contract-addresses) · [Arbitrum One](https://docs.arbitrum.io/arbitrum-bridge/quickstart)
5. Confira o crédito no histórico de depósitos e o saldo da conta Lighter. Ver USDC na carteira indica que o saque da corretora chegou à carteira. O crédito na Lighter aparece depois do depósito na plataforma.

## Comprar USDC com reais

- **Coinbase Brasil.** Cadastre o Pix na conta verificada, gere a solicitação de depósito de BRL e conclua o pagamento pelo seu banco. Após o crédito, compre ou converta para USDC. No saldo de USDC, escolha **Enviar**, informe o valor, selecione a rede compatível com a rota do depósito e revise o endereço, o destinatário e as taxas. Siga as verificações de destinatário que a Coinbase pedir no Brasil. Se a rota começar na sua carteira, informe o endereço da sua própria carteira. [Pix na Coinbase](https://help.coinbase.com/pt-br/coinbase/getting-started/add-a-payment-method/add-and-verify-pm-namerica-latam) · [Como enviar cripto no Brasil](https://help.coinbase.com/pt-br/coinbase/trading-and-funding/sending-or-receiving-cryptocurrency/send-receive-crypto-brazil)
- **Pix pela Binance Brasil ou OKX Brasil.** Verifique sua conta, abra o depósito de BRL e use o código Pix gerado na tela, a partir de uma conta bancária em seu nome. Depois que os reais aparecerem, compre ou converta para USDC. Na tela de saque confira o token, a rede, a taxa e o valor líquido recebido. [Guia da Binance Brasil](https://www.binance.com/pt-BR/support/faq/detail/53636607eebc42dbb513863b49bba98f) · [Guia da OKX Brasil](https://www.okx.com/pt-br/help/how-do-i-deposit-brl)
- **CriptoCore.** A documentação pública mostra depósito de cripto, crédito em USDT e uso desse saldo para pagar ou sacar via Pix em reais. Para financiar a Lighter com BRL, use a rota de Pix de entrada documentada acima. [CriptoCore](https://criptocore.net/)

## Conectar o EMA Trader

1. Na conta ou subconta da Lighter que você quer acompanhar, anote o **índice da conta** e crie uma chave de API vinculada a ela. Anote também o **índice da chave**. O índice da conta identifica a conta e o índice da chave identifica a credencial.
2. No EMA Trader, abra **Configurações → Ordens** e desbloqueie o cofre. Selecione **Mainnet** para a conta real. Informe o índice da conta e use **Só acompanhar conta** para verificar a posição. Confira o saldo disponível na interface da Lighter.
3. Para testar ordens com saldo de teste, use a Testnet e uma chave criada nessa rede. Para habilitar ordens, informe a chave privada da API, a margem base e a alavancagem no app. Guarde a frase de recuperação da carteira fora do app.
4. Mantenha o EMA Trader aberto para monitorar e executar sinais. O navegador pode ser fechado após configurar a conta.

## Operações com dinheiro real

Ao usar dinheiro real, acompanhe continuamente as posições, as ordens e a atuação do robô na conta correta. Se não puder acompanhar, desative as ordens automáticas. Use a [Testnet](https://testnet.app.lighter.xyz/) para aprender o fluxo com saldo de teste.

Se o robô falhar ou divergir da conta, desative a automação ou feche o app, se possível. Abra [app.lighter.xyz](https://app.lighter.xyz/), confira a conta e as ordens abertas e encerre manualmente a posição que precisa fechar. Confirme na Lighter que a posição zerou e que não há ordens pendentes indesejadas antes de reativar.

[Aviso de uso e riscos](RISK.md)

[Abrir a Testnet](https://testnet.app.lighter.xyz/) · [ORDERS](ORDERS.md) · [SUBACCOUNTS](SUBACCOUNTS.md) · [DATA](DATA.md)
