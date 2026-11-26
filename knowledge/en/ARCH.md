# ARCH · Structure and flows
- `app.py` starts the terminal or Tk window. The window uses one worker for polling and execution. `gui_entry.py` starts the packaged window.
- `engine.py` fetches and normalizes data, computes signals, handles missed turns and coordinates monitoring. `broker.py` authenticates and executes on Lighter. `storage.py` handles files and coordination across instances.
- Execution flow: closed candles → EMA → latest new turn → real position → close if needed → verify flat → new entry. See [SIGNALS](SIGNALS.md) and [ORDERS](ORDERS.md).
- `i18n.py` translates app text. Window language is saved per profile. The CLI uses `--lang pt|en|es`. Providers may return messages in their own language.
- `knowledge.py` resolves versioned topics. `local_mcp.py` serves a bounded view of the running instance independently of the exchange. [MCP](MCP.md)
