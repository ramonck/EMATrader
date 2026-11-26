# ARCH · Estrutura e fluxos
- `app.py` inicia terminal ou janela Tk. A janela usa um worker para consultas e execução. `gui_entry.py` inicia a janela empacotada.
- `engine.py` consulta e normaliza dados, calcula sinais, detecta viradas perdidas e coordena o monitor. `broker.py` autentica e executa na Lighter. `storage.py` grava arquivos e coordena instâncias.
- Fluxo de execução: candles fechados → EMA → última virada nova → posição real → fechamento, se necessário → confirmação de zeragem → nova entrada. Veja [SIGNALS](SIGNALS.md) e [ORDERS](ORDERS.md).
- `i18n.py` traduz textos do app. Idioma da janela é salvo por perfil; o terminal usa `--lang pt|en|es`. Mensagens dos provedores podem aparecer no idioma original.
- `knowledge.py` resolve tópicos versionados. `local_mcp.py` publica uma leitura limitada da instância ativa, independente da corretora. [MCP](MCP.md)
