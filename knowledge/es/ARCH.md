# ARCH · Estructura y flujos
- `app.py` inicia la terminal o la ventana Tk. La ventana usa un trabajador para la consulta y ejecución. `gui_entry.py` inicia la ventana empaquetada.
- `engine.py` consulta y normaliza los datos, calcula señales, recupera giros omitidos y coordina el monitor. `broker.py` autentica y ejecuta en Lighter. `storage.py` gestiona archivos y coordina instancias.
- Flujo de ejecución: velas cerradas → EMA → último giro nuevo → posición real → cierre si corresponde → verificar posición nula → nueva entrada. Véanse [SIGNALS](SIGNALS.md) y [ORDERS](ORDERS.md).
- `i18n.py` traduce la aplicación. El idioma de la ventana se guarda por perfil. La terminal usa `--lang pt|en|es`. Los proveedores pueden devolver mensajes en su idioma original.
- `knowledge.py` resuelve temas versionados. `local_mcp.py` ofrece una vista limitada de la instancia activa, independiente de la bolsa. [MCP](MCP.md)
