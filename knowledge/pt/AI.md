# AI · Contexto compacto para assistentes
- O EMA Trader entrega dados sob demanda por MCP. O parecer fica no assistente que você conectar. As ferramentas MCP consultam a posição, P&L, idade dos dados e os resumos dos ativos visto e armado, sem chamar a corretora.
- Comece por `status`. Ele inclui preço, direção, limites da EMA, variação das duas EMAs em 22 velas, faixa, variação de preço e volume relativo de até 24 candles. Os horários em milissegundos UTC mostram quão recente é cada dado.
- Peça `candles` só se precisar dos candles individuais, com um limite de 1 a 24. Para regras use `knowledge_index` e `knowledge_rule` com o mesmo idioma. Evite carregar o repositório ou as três traduções de uma vez.
