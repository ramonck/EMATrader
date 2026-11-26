# RECONNECT · Actualización y recuperación
- La aplicación consulta cada cinco minutos, alineada al reloj, y reintenta cada dos minutos si falla la lectura. Sigue minimizada. Suspender, apagar o cerrar el proceso interrumpe el monitor.
- El cursor empieza al activar. Tras reconectar, el último giro direccional cerrado posterior al cursor es elegible. Se omiten los giros intermedios y se usa el precio disponible al ejecutar. Gris no borra el giro.
- El registro guarda vela y orden pendiente antes del envío. Si no se sabe el resultado, se pausa para conciliar. Un proceso nuevo comienza en modo de seguimiento.
- Código `Monitor.snapshot`, `take_signal` y `broker.execute`.
