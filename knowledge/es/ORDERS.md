# ORDERS · Posición real, adopción y ejecución
- El modo inicial sigue el mercado. Las órdenes requieren la clave de la subcuenta y habilitación explícita de Mainnet. Al habilitar, se consulta el activo seleccionado bajo el bloqueo de la cuenta y se asume automáticamente toda la posición y lado que informa Lighter, incluso si se abrió manualmente. Activar no envía órdenes y solo acepta señales futuras.
- Órdenes activas en el mercado, ejecución pendiente en su registro o posición nula con registro discrepante bloquean la adopción. Una posición en otro mercado impide habilitar un activo sin posición y bloquea nuevas entradas en la cuenta.
- El primer giro nuevo contrario a la posición cierra el tamaño real con una orden de mercado `reduce_only`. Un llenado parcial puede provocar intentos de cierre del resto. Se exige confirmar posición nula antes de abrir al lado inverso. Si no se concilia, se pone en pausa.
- El margen configurado y el apalancamiento de hasta 20× se aplican a nuevas posiciones, sujetos al límite del mercado. El límite de precio usa profundidad del libro. La falta de liquidez puede impedir el cierre total.
- Cambiar el gráfico conserva el mercado activado. Si tiene una posición, la ventana vuelve a él al actualizar tras cinco minutos de navegación. Un pitido opcional indica una acción confirmada.
- Código `Monitor.arm`, `broker.execute`, `broker.connect`. [RECONNECT](RECONNECT.md) · [DATA](DATA.md)
- Elimina `--adopt-size` de comandos antiguos. La posición se consulta automáticamente al asumirla.
