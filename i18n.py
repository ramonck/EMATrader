"""Translations for app-owned messages. Provider errors retain their original text."""

import re
from string import Formatter

LANGUAGES = {"pt": "Português", "en": "English", "es": "Español"}

MESSAGES = {
    "Cofre local": ("Local vault", "Bóveda local"),
    "Desbloquear cofre": ("Unlock vault", "Desbloquear bóveda"),
    "Frase secreta do cofre": ("Vault passphrase", "Frase secreta de la bóveda"),
    "Repita a frase secreta": ("Repeat the passphrase", "Repite la frase secreta"),
    "As frases secretas não coincidem.": ("Passphrases do not match.", "Las frases secretas no coinciden."),
    "Salvar chave no cofre": ("Save key to vault", "Guardar clave en la bóveda"),
    "Ler histórico privado de ordens": ("Read private order history", "Leer el historial privado de órdenes"),
    "Desbloqueie o cofre para usar a conta da Lighter.": (
        "Unlock the vault to use the Lighter account.", "Desbloquea la bóveda para usar la cuenta de Lighter."),
    "Abra um terminal interativo ou defina EMA_TRADER_VAULT_PASSPHRASE.": (
        "Use an interactive terminal or set EMA_TRADER_VAULT_PASSPHRASE.",
        "Usa una terminal interactiva o define EMA_TRADER_VAULT_PASSPHRASE."),
    "Use uma frase secreta de pelo menos 12 caracteres para o cofre.": (
        "Use a vault passphrase of at least 12 characters.", "Usa una frase secreta de al menos 12 caracteres."),
    "Metadados do cofre inválidos.": ("Invalid vault metadata.", "Metadatos de bóveda inválidos."),
    "Frase secreta incorreta ou cofre danificado.": (
        "Incorrect passphrase or damaged vault.", "Frase secreta incorrecta o bóveda dañada."),
    "Registro privado inválido ou adulterado.": (
        "Invalid or modified private record.", "Registro privado inválido o alterado."),
    "Buscar ativo": ("Find asset", "Buscar activo"),
    "Limite de perda da conta (%)": ("Account drawdown limit (%)", "Límite de caída de la cuenta (%)"),
    "Limite de perda da conta inválido.": ("Invalid account drawdown limit.", "Límite de caída de la cuenta inválido."),
    "Saldo total da conta indisponível.": ("Account equity unavailable.", "Patrimonio de la cuenta no disponible."),
    "Limite de perda da conta atingido. Automação pausada.": (
        "Account drawdown limit reached. Automation paused.", "Se alcanzó el límite de caída de la cuenta. Automatización en pausa."),
    "A conta continua pausada. Zere a posição antes de reiniciar o limite de perda.": (
        "The account is still paused. Close the position before resetting the drawdown limit.",
        "La cuenta sigue en pausa. Cierra la posición antes de reiniciar el límite de caída."),
    "Margem base USD": ("Base margin (USD)", "Margen base (USD)"),
    "Sem saldo disponível para a próxima operação.": (
        "No available balance for the next trade.", "No hay saldo disponible para la próxima operación."),
    "O saldo disponível mudou antes do envio da ordem.": (
        "The available balance changed before order submission.", "El saldo disponible cambió antes de enviar la orden."),
    "Não foi possível conciliar o saldo para reinvestir.": (
        "Could not reconcile the balance for reinvestment.",
        "No se pudo conciliar el saldo para reinvertir."),
    "Defina EMA_TRADER_MCP_TOKEN para habilitar o MCP no terminal.": (
        "Set EMA_TRADER_MCP_TOKEN to enable MCP in the terminal.",
        "Define EMA_TRADER_MCP_TOKEN para activar MCP en la terminal."),
    "O token MCP precisa ter pelo menos 24 letras ASCII ou dígitos.": (
        "The MCP token must contain at least 24 ASCII letters or digits.",
        "El token MCP debe tener al menos 24 letras ASCII o dígitos."),
    "Aguardando candles fechados de 15 min": ("Waiting for closed 15-minute candles", "Esperando velas cerradas de 15 minutos"),
    "Conta não configurada": ("Account not configured", "Cuenta sin configurar"),
    "Atualizar": ("Refresh", "Actualizar"),
    "Configurações": ("Settings", "Configuración"),
    "AL abre long · FL fecha long · AS abre short · FS fecha short": (
        "AL opens long · FL closes long · AS opens short · FS closes short",
        "AL abre long · FL cierra long · AS abre short · FS cierra short"),
    "Novas ordens neste gráfico estão bloqueadas.": (
        "New orders on this chart are blocked.", "Las nuevas órdenes en este gráfico están bloqueadas."),
    "Subcontas": ("Subaccounts", "Subcuentas"),
    "Conta na Lighter": ("Lighter account", "Cuenta en Lighter"),
    "Verde: long · Vermelho: short · Cinza: mantém": ("Green: long · Red: short · Gray: hold", "Verde: long · Rojo: short · Gris: mantener"),
    "Zerado": ("Flat", "Sin posición"),
    "Manter {side}": ("Hold {side}", "Mantener {side}"),
    "Quantidade {quantity} · entrada {price}": ("Size {quantity} · entry {price}", "Cantidad {quantity} · entrada {price}"),
    "Dados desatualizados": ("Stale data", "Datos desactualizados"),
    "Sem posição aberta": ("No open position", "Sin posición abierta"),
    "Aguardando conta": ("Waiting for account data", "Esperando datos de la cuenta"),
    "Ordens automáticas ativas para {symbol}": ("Automatic orders enabled for {symbol}", "Órdenes automáticas activas para {symbol}"),
    "Ordens automáticas desativadas": ("Automatic orders disabled", "Órdenes automáticas desactivadas"),
    "Subcontas Lighter": ("Lighter subaccounts", "Subcuentas de Lighter"),
    "Abrir documentação oficial?": ("Open the official documentation?", "¿Abrir la documentación oficial?"),
    "Rede": ("Network", "Red"),
    "Índice da conta": ("Account index", "Índice de la cuenta"),
    "Índice da chave": ("Key index", "Índice de la clave"),
    "Chave privada": ("Private key", "Clave privada"),
    "Margem USD": ("Margin (USD)", "Margen (USD)"),
    "Alavancagem": ("Leverage", "Apalancamiento"),
    "Idioma": ("Language", "Idioma"),
    "Um beep por ação confirmada": ("One beep per confirmed action", "Un pitido por acción confirmada"),
    "Aguarde a consulta atual terminar.": ("Wait for the current request to finish.", "Espera a que termine la consulta actual."),
    "Índice inválido.": ("Invalid index.", "Índice inválido."),
    "Ativar ordens automáticas reais para {symbol}?": ("Enable live automatic orders for {symbol}?", "¿Activar órdenes automáticas reales para {symbol}?"),
    "Só acompanhar conta": ("Monitor account only", "Solo seguir la cuenta"),
    "Ativar ordens automáticas": ("Enable automatic orders", "Activar órdenes automáticas"),
    "Pasta de históricos": ("History folder", "Carpeta de historiales"),
    "Aguarde a consulta ou a execução em andamento terminar.": ("Wait for the current request or execution to finish.", "Espera a que termine la consulta o ejecución en curso."),
    "EMA Trader · faixa EMA de 15 minutos": ("EMA Trader · 15-minute EMA band", "EMA Trader · banda EMA de 15 minutos"),
    "abrir a interface gráfica": ("open the desktop interface", "abrir la interfaz gráfica"),
    "preferências separadas da janela": ("separate window preferences", "preferencias independientes de la ventana"),
    "mostrar guia de subcontas": ("show subaccount guide", "mostrar la guía de subcuentas"),
    "Confira a conta, chave, margem e alavancagem.": ("Check the account, key, margin and leverage.", "Comprueba la cuenta, la clave, el margen y el apalancamiento."),
    "Informe --account; para ordens reais, também --confirm-mainnet.": ("Set --account. For live orders, also set --confirm-mainnet.", "Indica --account. Para órdenes reales, indica también --confirm-mainnet."),
    "Abrir long": ("Open long", "Abrir long"),
    "Fechar long": ("Close long", "Cerrar long"),
    "Abrir short": ("Open short", "Abrir short"),
    "Fechar short": ("Close short", "Cerrar short"),
    "Desative a automação atual antes de trocar de conta, rede ou ativo.": ("Disable the current automation before changing the account, network or asset.", "Desactiva la automatización actual antes de cambiar de cuenta, red o activo."),
    "Candles fechados desatualizados.": ("Closed candles are stale.", "Las velas cerradas están desactualizadas."),
    "Execução pausada. Confira posição e diário.": ("Execution paused. Check your position and journal.", "Ejecución en pausa. Comprueba tu posición y el registro."),
    "O diário tem uma ordem pendente para este mercado. Concilie antes de assumir a posição.": ("The journal has a pending order for this market. Reconcile it before adopting the position.", "El registro tiene una orden pendiente para este mercado. Concíliala antes de asumir la posición."),
    "Há ordem ativa ou pendente neste mercado. Confira antes de assumir.": ("This market has an active or pending order. Check it before adoption.", "Hay una orden activa o pendiente en este mercado. Revísala antes de asumir la posición."),
    "Estado da posição divergente ou ordem pendente. Confira a conta e o diário antes de retomar.": ("Position mismatch or pending order. Check the account and journal before resuming.", "Posición discrepante u orden pendiente. Comprueba la cuenta y el registro antes de reanudar."),
    "A conta já tem posição aberta. Novas entradas estão bloqueadas.": ("The account already has an open position. New entries are blocked.", "La cuenta ya tiene una posición abierta. Las nuevas entradas están bloqueadas."),
    "Há ordens ativas ou pendentes na conta. Novas entradas estão bloqueadas.": ("The account has active or pending orders. New entries are blocked.", "La cuenta tiene órdenes activas o pendientes. Las nuevas entradas están bloqueadas."),
    "Há uma execução pendente no diário desta conta.": ("The account journal has a pending execution.", "El registro de la cuenta tiene una ejecución pendiente."),
    "A chave informada não corresponde à conta ou à rede da Lighter.": ("The key does not match the Lighter account or network.", "La clave no coincide con la cuenta o la red de Lighter."),
    "A Lighter não retornou a conta selecionada.": ("Lighter did not return the selected account.", "Lighter no devolvió la cuenta seleccionada."),
    "Não foi possível autenticar a chave da Lighter.": ("Could not authenticate the Lighter key.", "No se pudo autenticar la clave de Lighter."),
    "Não foi possível bloquear o diário da conta. Confira o armazenamento e outras instâncias.": ("Could not lock the account journal. Check storage and other instances.", "No se pudo bloquear el registro de la cuenta. Comprueba el almacenamiento y las otras instancias."),
    "Execução não conciliada. O diário bloqueou outros envios até revisão da ordem.": ("Execution not reconciled. The journal blocked further orders until review.", "Ejecución sin conciliar. El registro bloqueó más órdenes hasta su revisión."),
    "A consulta foi rejeitada.": ("The request was rejected.", "Se rechazó la consulta."),
    "A resposta excedeu o tamanho esperado.": ("The response exceeded the expected size.", "La respuesta superó el tamaño esperado."),
    "Símbolo inválido.": ("Invalid symbol.", "Símbolo inválido."),
    "Símbolo Lighter inválido.": ("Invalid Lighter symbol.", "Símbolo de Lighter inválido."),
    "Índices de conta ou chave inválidos.": ("Invalid account or key index.", "Índice de cuenta o clave inválido."),
    "Livro de ofertas sem preço disponível.": ("The order book has no available price.", "El libro de órdenes no tiene precios disponibles."),
    "Livro de ofertas incompleto.": ("Incomplete order book.", "Libro de órdenes incompleto."),
    "Livro de ofertas vazio para executar a ordem.": ("The order book is empty for this order.", "El libro de órdenes está vacío para esta orden."),
    "Margem, alavancagem ou desvio de preço inválido.": ("Invalid margin, leverage or price deviation.", "Margen, apalancamiento o desviación de precio inválidos."),
    "A posição mudou durante a configuração da alavancagem.": ("The position changed while configuring leverage.", "La posición cambió al configurar el apalancamiento."),
    "A Lighter ainda não confirmou a margem isolada e a alavancagem.": ("Lighter has yet to confirm isolated margin and leverage.", "Lighter aún no ha confirmado el margen aislado y el apalancamiento."),
    "Quantidade abaixo do mínimo da Lighter.": ("Quantity below Lighter's minimum.", "Cantidad inferior al mínimo de Lighter."),
    "Mercado perpétuo {symbol} ativo não identificado na Lighter.": ("Active perpetual market {symbol} was not found on Lighter.", "No se encontró el mercado perpetuo activo {symbol} en Lighter."),
    "Há ordens {symbol} abertas na conta selecionada.": ("The selected account has open {symbol} orders.", "La cuenta seleccionada tiene órdenes abiertas de {symbol}."),
    "Alavancagem acima do limite do mercado {symbol}.": ("Leverage exceeds the {symbol} market limit.", "El apalancamiento supera el límite del mercado {symbol}."),
    "Quantidade {symbol} incompatível com a precisão do mercado.": ("The {symbol} size does not match the market precision.", "La cantidad de {symbol} no coincide con la precisión del mercado."),
    "Lighter não confirmou o envio de {action}. Consulte a conta.": ("Lighter did not confirm the {action} submission. Check the account.", "Lighter no confirmó el envío de {action}. Consulta la cuenta."),
    "{symbol}: mercado indisponível no catálogo da Lighter.": ("{symbol}: market unavailable in the Lighter catalog.", "{symbol}: mercado no disponible en el catálogo de Lighter."),
    "Conta": ("Account", "Cuenta"),
    "MCP local": ("Local MCP", "MCP local"),
    "Ativar MCP local": ("Enable local MCP", "Activar MCP local"),
    "Porta MCP": ("MCP port", "Puerto MCP"),
    "Token MCP": ("MCP token", "Token MCP"),
    "Copiar token": ("Copy token", "Copiar token"),
    "Desativar MCP": ("Disable MCP", "Desactivar MCP"),
    "MCP ativo em {url}": ("MCP listening at {url}", "MCP activo en {url}"),
    "Idioma e MCP": ("Language and MCP", "Idioma y MCP"),
    "Ordens": ("Orders", "Órdenes"),
    "Pronto": ("Ready", "Listo"),
    "Abrir histórico": ("Open history", "Abrir historial"),
    "Porta inválida.": ("Invalid port.", "Puerto inválido."),
    "Nenhum dado recente está disponível.": ("No recent data is available.", "No hay datos recientes disponibles."),
    "Faixa EMA": ("EMA band", "Banda EMA"),
    "usar consulta local via MCP na porta indicada": ("serve local MCP queries on the specified port", "servir consultas MCP locales en el puerto indicado"),
    "Ajustes salvos.": ("Settings saved.", "Configuración guardada."),
}


def tr(language, message, **values):
    if language in ("en", "es") and message in MESSAGES:
        message = MESSAGES[message][int(language == "es")]
    return message.format(**values) if values else message


ERROR_PATTERNS = [
    (re.compile("".join(re.escape(text) + (f"(?P<{field}>.+)" if field else "")
                        for text, field, _, _ in Formatter().parse(message))), message)
    for message in MESSAGES if "{" in message
]


def translate_error(language, error):
    message = str(error)
    if language == "pt" or message in MESSAGES:
        return tr(language, message)
    for pattern, template in ERROR_PATTERNS:
        match = pattern.fullmatch(message)
        if match:
            return tr(language, template, **match.groupdict())
    prefix, separator, detail = message.partition(": ")
    if separator and detail and prefix:
        return f"{tr(language, prefix)}: {translate_error(language, detail)}"
    return message
