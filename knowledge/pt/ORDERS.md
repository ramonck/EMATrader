# ORDERS · Posição real, adoção e execução
- O modo padrão acompanha. Ativar ordens exige chave da subconta e habilitação explícita de Mainnet. A ativação lê o ativo selecionado na conta sob trava e assume sua posição real automaticamente, inclusive manual, na quantidade integral e com o lado retornado pela Lighter. A ativação por si só não envia ordem e só aceita sinais futuros.
- Ordens ativas no mercado, execução pendente no seu diário ou posição zerada com diário divergente bloqueiam a adoção. Posição aberta em outro mercado impede iniciar a automação em um ativo zerado. Uma posição em outro mercado impede novas entradas na conta.
- Ao surgir a primeira virada nova contrária à posição, fecha a quantidade real com ordem de mercado `reduce_only`. Se houver execução parcial, tenta fechar o restante e exige confirmação de posição zerada antes da abertura inversa. Se não conciliar, pausa.
- Margem configurada e alavancagem de até 20× se aplicam às novas posições, respeitando o limite do mercado. O preço limite da ordem usa a profundidade do livro. Liquidez insuficiente pode impedir zeragem.
- Trocar o gráfico mantém o mercado armado. Havendo posição nele, a janela volta para esse mercado após a janela de navegação de cinco minutos, na próxima atualização. Alerta sonoro opcional por ação confirmada.
- Código `Monitor.arm`, `broker.execute`, `broker.connect`. [RECONNECT](RECONNECT.md) · [DATA](DATA.md)
- Remova `--adopt-size` de comandos antigos. A leitura da posição para adoção é automática.
