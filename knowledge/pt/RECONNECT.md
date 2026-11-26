# RECONNECT · Atualização e recuperação
- O app consulta a cada cinco minutos, alinhado ao relógio, e tenta novamente a cada dois minutos quando leituras falham. Continua minimizado. Suspensão, desligamento ou fechamento do processo interrompem o monitor.
- O cursor começa na ativação. Após reconectar, a última virada direcional fechada posterior ao cursor é elegível; viradas intermediárias são ignoradas. Usa o preço disponível no momento da execução. Cinza não apaga a virada.
- O diário registra candle e ordem pendente antes do envio. Se a execução ficou incerta, o app pausa a automação para conciliação. Um novo processo começa em modo de acompanhamento.
- Código `Monitor.snapshot`, `take_signal` e `broker.execute`.
