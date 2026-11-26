"""Lighter execution, account-wide locking and reconciled order journal."""
import asyncio
import json
import os
import sys
import time
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
from storage import account_lock, data_root
from vault import Vault

NETWORKS = {
    "testnet": "https://testnet.zklighter.elliot.ai",
    "mainnet": "https://mainnet.zklighter.elliot.ai",
}


class BridgeError(Exception):
    pass


def next_margin(base, used, pnl):
    return base if pnl < 0 else max(base, used + pnl)


RISK_HALT = "Limite de perda da conta atingido. Automação pausada."
PRICE_CANCEL = "canceled-too-much-slippage"
CLOSE_PENDING = "A posição ainda não zerou. A abertura inversa ficou bloqueada."


def retryable_entry(result):
    return (result.get("action") in ("Abrir long", "Abrir short")
            and result.get("status") == PRICE_CANCEL
            and Decimal(result["filled"]) == 0 and Decimal(result["position"]) == 0)


def entry_pause_reason(result):
    if result.get("risk_halt"):
        return RISK_HALT
    if result.get("entry_skipped"):
        return "A entrada foi bloqueada antes do envio à Lighter."
    if not result.get("partial"):
        return None
    filled, status = result["filled"], result["status"]
    if status == PRICE_CANCEL and Decimal(filled) == 0:
        return "A Lighter cancelou a abertura por desvio de preço. Quantidade executada: 0."
    if Decimal(filled) == 0:
        return f"A abertura terminou sem execução na Lighter. Status: {status}."
    return f"A abertura foi executada parcialmente na Lighter. Quantidade: {filled}. Status: {status}."


def account_risk(state_path, request, snapshot, rearm=False):
    percent = Decimal(str(request.get("drawdown", 0)))
    if not 0 < percent < 100:
        raise BridgeError("Limite de perda da conta inválido.")
    equity = Decimal(snapshot.total_asset_value)
    if not equity.is_finite():
        raise BridgeError("Saldo total da conta indisponível.")
    path = state_path.parent / "risk" / f'{request["network"]}-{request["account"]}.json'
    vault = request["vault"]
    saved = state = vault.read(path, {})
    if rearm and state.get("halted"):
        if any(Decimal(row.position) for row in snapshot.positions):
            raise BridgeError("A conta continua pausada. Zere a posição antes de reiniciar o limite de perda.")
        state = {}
    peak = max(equity, Decimal(state.get("peak", 0)))
    halted = bool(state.get("halted")) or (peak > 0 and equity <= peak * (1 - percent / 100))
    updated = {"peak": str(peak), "halted": halted}
    if updated != saved:
        vault.write(path, updated)
    return halted


async def account_snapshot(sdk, client, account):
    result = await sdk.AccountApi(client.api_client).account(by="index", value=str(account), active_only=False)
    if len(result.accounts) != 1 or result.accounts[0].index != account:
        raise BridgeError("A Lighter não retornou a conta selecionada.")
    return result.accounts[0]


async def position(sdk, client, account, market):
    snapshot = await account_snapshot(sdk, client, account)
    return market_position(snapshot, market)


def market_position(snapshot, market):
    row = next((p for p in snapshot.positions if p.market_id == market), None)
    return (Decimal(row.position) * row.sign, row) if row else (Decimal(0), None)


def public_positions(snapshot):
    return [{"symbol": row.symbol, "position": row.position, "sign": row.sign,
             "avg_entry_price": row.avg_entry_price, "unrealized_pnl": row.unrealized_pnl}
            for row in snapshot.positions if Decimal(row.position) != 0]


async def ensure_account_flat(sdk, client, account, auth, state_path, vault):
    snapshot = await account_snapshot(sdk, client, account)
    if any(Decimal(row.position) != 0 for row in snapshot.positions):
        raise BridgeError("A conta já tem posição aberta. Novas entradas estão bloqueadas.")
    active = await client.order_api.account_active_orders(auth, account)
    if active.orders or snapshot.pending_order_count:
        raise BridgeError("Há ordens ativas ou pendentes na conta. Novas entradas estão bloqueadas.")
    prefix = state_path.stem.split("-", 2)[:2]
    for journal in state_path.parent.glob("-".join(prefix) + "*.json"):
        name = journal.stem.split("-", 2)
        if name[:2] == prefix and vault.read(journal).get("pending"):
            raise BridgeError("Há uma execução pendente no diário desta conta.")
    return snapshot


def acknowledge(result, action):
    _, response, error = result
    if error or response is None or response.code != 200:
        raise BridgeError(f"Lighter não confirmou o envio de {action}. Consulte a conta.")
    return response


async def execution_quote(client, market_id, selling, entry_levels):
    prices = await client.order_api.order_book_orders(market_id, 1)
    side = prices.bids if selling else prices.asks
    if not side:
        raise BridgeError("Livro de ofertas sem preço disponível.")
    quote = Decimal(side[0].price)
    if entry_levels is None:
        return quote
    if not prices.bids or not prices.asks:
        raise BridgeError("Livro de ofertas incompleto.")
    low, high = entry_levels
    upside, downside = high - quote, quote - low
    spread = Decimal(prices.asks[0].price) - Decimal(prices.bids[0].price)
    cost = max(spread, quote * Decimal("0.0002"))
    room, risk = (downside, upside) if selling else (upside, downside)
    return quote if min(room, risk) > 0 and room - cost >= risk else None


async def market_depth_price(client, market_id, selling, quantity):
    prices = await client.order_api.order_book_orders(market_id, 50)
    orders = prices.bids if selling else prices.asks
    depth = Decimal(0)
    last_price = None
    for order in sorted(orders, key=lambda row: Decimal(row.price), reverse=selling):
        remaining = Decimal(order.remaining_base_amount)
        if remaining <= 0:
            continue
        depth += remaining
        last_price = Decimal(order.price)
        if depth >= quantity:
            break
    if last_price is None:
        raise BridgeError("Livro de ofertas vazio para executar a ordem.")
    return last_price


async def execute(sdk, client, request, account, key_index, state_path, continue_rotation=False):
    vault = request["vault"]
    result = await client.order_api.order_book_details()
    symbol = request.get("symbol", "BTC")
    command = request["command"]
    markets = [m for m in result.order_book_details if m.symbol == symbol and m.market_type == "perp" and m.status == "active"]
    if len(markets) != 1:
        raise BridgeError(f"Mercado perpétuo {symbol} ativo não identificado na Lighter.")
    market = markets[0]
    market_id = market.market_id
    auth, error = client.create_auth_token_with_expiry(api_key_index=key_index)
    if error or not auth:
        raise BridgeError("Não foi possível autenticar a chave da Lighter.")
    snapshot = await account_snapshot(sdk, client, account)
    current, config = market_position(snapshot, market_id)
    state = vault.read(state_path, {"position": "0", "candle": -1})
    if command == "check":
        blocked = None
        if request.get("single_position") and not current:
            try:
                await ensure_account_flat(sdk, client, account, auth, state_path, vault)
            except BridgeError as error:
                blocked = str(error)
        return {"position": str(current), "market": market_id, "breakout_filter": True, "entry_room_filter": True,
                "pending": bool(state.get("pending")), "blocked": blocked, "positions": public_positions(snapshot),
                "ready": not state.get("pending") and Decimal(state["position"]) == current}
    if command == "arm":
        if state.get("pending"):
            raise BridgeError("O diário tem uma ordem pendente para este mercado. Concilie antes de assumir a posição.")
        if not current:
            await ensure_account_flat(sdk, client, account, auth, state_path, vault)
            if Decimal(state["position"]):
                raise BridgeError("Estado da posição divergente ou ordem pendente. Confira a conta e o diário antes de retomar.")
        else:
            active = await client.order_api.account_active_orders(auth, account, market_id)
            if active.orders or config.pending_order_count:
                raise BridgeError("Há ordem ativa ou pendente neste mercado. Confira antes de assumir.")
            if Decimal(state["position"]) != current:
                state.pop("reinvestment", None)
                vault.write(state_path, dict(state, position=str(current), adopted_at=int(time.time() * 1000)))
        if request.get("drawdown") and account_risk(state_path, request, snapshot, rearm=True):
            raise BridgeError(RISK_HALT)
        return {"ready": True, "position": str(current), "market": market_id, "positions": public_positions(snapshot)}
    if state.get("pending") or Decimal(state["position"]) != current:
        raise BridgeError("Estado da posição divergente ou ordem pendente. Confira a conta e o diário antes de retomar.")
    risk_halt = request.get("drawdown") and account_risk(state_path, request, snapshot)
    if (not current and risk_halt) or (command == "risk" and not risk_halt):
        return {"position": str(current), "risk_halt": bool(risk_halt)}
    if risk_halt:
        candle = max(int(time.time() * 1000), state["candle"] + 1)
        raw_direction = -1 if current > 0 else 1
        command = "rotate"
    else:
        candle = int(request["candle"])
        raw_direction = int(request["direction"])
    if raw_direction not in (-1, 1) or candle < state["candle"] or (
        candle == state["candle"] and not continue_rotation
    ):
        return {"position": str(current)}
    target = Decimal(raw_direction)
    if current * target > 0:
        return {"position": str(current)}
    if not current and not request.get("allow_open", True):
        return {"position": "0", **({"entry_skipped": "entrada desativada"} if request.get("entry_signal") else {})}
    if current and request.get("only_open", False):
        return {"position": str(current)}
    active = await client.order_api.account_active_orders(auth, account, market_id)
    if active.orders:
        raise BridgeError(f"Há ordens {symbol} abertas na conta selecionada.")

    base_margin = Decimal(str(request["margin"]))
    margin = base_margin
    leverage = int(request["leverage"])
    book_price = command == "rotate" and "slippage" not in request
    slippage = Decimal(str(request.get("slippage", 0))) / 100
    if not (0 < margin <= 1000000 and 1 <= leverage <= 20 and
            (book_price or 0 < slippage <= Decimal("0.05"))):
        raise BridgeError("Margem, alavancagem ou desvio de preço inválido.")
    closing = current != 0
    compound = request.get("compound") and command == "rotate"
    selling = current > 0 if closing else target < 0
    entry_levels = None
    if not closing and "prior_high" in request:
        entry_levels = (Decimal(str(request["prior_low"])), Decimal(str(request["prior_high"])))
    quote = await execution_quote(client, market_id, selling, entry_levels)
    if quote is None:
        return {"position": "0", "entry_skipped": "livro Lighter"}
    if not closing:
        if command == "rotate":
            await ensure_account_flat(sdk, client, account, auth, state_path, vault)
        fraction = 10000 // leverage
        if fraction < market.min_initial_margin_fraction:
            raise BridgeError(f"Alavancagem acima do limite do mercado {symbol}.")
        isolated = sdk.SignerClient.ISOLATED_MARGIN_MODE
        if config is None or config.margin_mode != isolated or Decimal(config.initial_margin_fraction) * 100 != fraction:
            acknowledge(await client.update_leverage(market_id, isolated, leverage, api_key_index=key_index),
                        "alavancagem")
            for _ in range(8):
                await asyncio.sleep(1)
                current, config = await position(sdk, client, account, market_id)
                if current:
                    raise BridgeError("A posição mudou durante a configuração da alavancagem.")
                if config is not None and config.margin_mode == isolated and Decimal(config.initial_margin_fraction) * 100 == fraction:
                    break
            else:
                raise BridgeError("A Lighter ainda não confirmou a margem isolada e a alavancagem.")
            quote = await execution_quote(client, market_id, selling, entry_levels)
            if quote is None:
                return {"position": "0", "entry_skipped": "livro Lighter"}
        if compound:
            snapshot = await account_snapshot(sdk, client, account)
            available = Decimal(snapshot.available_balance)
            saved_margin = state.get("reinvestment", {})
            if Decimal(saved_margin.get("base", base_margin)) == base_margin:
                margin = max(base_margin, Decimal(saved_margin.get("next", base_margin)))
            if not available.is_finite() or available <= 0:
                raise BridgeError("Sem saldo disponível para a próxima operação.")
            margin = min(margin, available)
            state["reinvestment"] = {"base": str(base_margin), "next": str(margin), "before": str(available)}

    size_scale = Decimal(10) ** market.size_decimals
    price_scale = Decimal(10) ** market.price_decimals
    base = abs(current) if closing else margin * leverage / (quote * (1 + slippage))
    market_limit = await market_depth_price(client, market_id, selling, base) if book_price else None
    if book_price and not closing:
        base = min(base, margin * leverage / market_limit)
    amount = int(base * size_scale)
    if amount <= 0 or (closing and Decimal(amount) / size_scale != base):
        raise BridgeError(f"Quantidade {symbol} incompatível com a precisão do mercado.")
    if not closing and (Decimal(amount) / size_scale < Decimal(market.min_base_amount) or
                        Decimal(amount) / size_scale * quote < Decimal(market.min_quote_amount)):
        raise BridgeError("Quantidade abaixo do mínimo da Lighter.")
    if not closing and command == "rotate":
        flat = await ensure_account_flat(sdk, client, account, auth, state_path, vault)
        if compound:
            available = Decimal(flat.available_balance)
            if not available.is_finite() or available < margin:
                raise BridgeError("O saldo disponível mudou antes do envio da ordem.")
            state["reinvestment"]["before"] = str(available)
    bound = (market_limit if book_price else quote * (1 - slippage if selling else 1 + slippage)) * price_scale
    limit = int(bound.to_integral_value(rounding=ROUND_CEILING if selling else ROUND_FLOOR))
    order_index = max(time.time_ns() // 1_000_000, int(state.get("last", {}).get("order", 0)) + 1)
    action = ("Fechar long" if current > 0 else "Fechar short") if closing else ("Abrir short" if selling else "Abrir long")
    vault.write(state_path, dict(state, position=str(current), candle=candle, pending=order_index, action=action))
    sent = acknowledge(await client.create_market_order(
        market_id, order_index, amount, limit, selling, reduce_only=closing, api_key_index=key_index), "ordem")
    for _ in range(12):
        await asyncio.sleep(1)
        orders = await client.order_api.account_inactive_orders(auth, account, 20, market_id)
        order = next((o for o in orders.orders if o.client_order_index == order_index), None)
        if order is None:
            continue
        filled = Decimal(order.filled_base_amount)
        expected = current + (-filled if selling else filled)
        reinvestment = state.get("reinvestment")
        if compound and closing and not expected and reinvestment and "before" in reinvestment:
            settled = await account_snapshot(sdk, client, account)
            after, _ = market_position(settled, market_id)
            if not after:
                actual = Decimal(settled.available_balance)
                if not actual.is_finite() or any(Decimal(row.position) for row in settled.positions):
                    raise BridgeError("Não foi possível conciliar o saldo para reinvestir.")
                pnl = actual - Decimal(reinvestment["before"])
                used = Decimal(reinvestment["next"]) if Decimal(reinvestment["base"]) == base_margin else base_margin
                reinvestment = {"base": str(base_margin), "next": str(next_margin(base_margin, used, pnl)),
                                "pnl": str(pnl)}
                state["reinvestment"] = reinvestment
        else:
            after, _ = await position(sdk, client, account, market_id)
        if after != expected:
            continue
        report = {"position": str(after), "action": action, "filled": str(filled), "order": str(order_index),
                  "price": str(Decimal(order.filled_quote_amount) / filled) if filled else "0",
                  "status": order.status, "hash": sent.tx_hash, "time": order.updated_at,
                  "partial": filled < Decimal(amount) / size_scale}
        if risk_halt:
            report["risk_halt"] = True
        if compound and closing and not after and reinvestment and "pnl" in reinvestment:
            report.update(reinvestment_pnl_usd=reinvestment["pnl"], next_margin_usd=reinvestment["next"])
        if compound and not closing and not after:
            state["reinvestment"].pop("before", None)
        audit = dict(report, network=request["network"], candle=candle,
                     trigger="Account drawdown" if risk_halt else request.get("trigger"), margin_usd=str(margin),
                     leverage=leverage, account=account, symbol=symbol)
        vault.append_order(audit)
        state.pop("pending", None)
        state.pop("action", None)
        if not compound:
            state.pop("reinvestment", None)
        vault.write(state_path, dict(state, position=str(after), candle=candle, last=report))
        return report
    raise BridgeError("Execução não conciliada. O diário bloqueou outros envios até revisão da ordem.")


async def main(request):
    import lighter
    account = int(request["account"])
    key_index = int(request["key_index"])
    network = request["network"]
    if not isinstance(request.get("vault"), Vault) or request["vault"].root != data_root().resolve():
        raise BridgeError("Desbloqueie o cofre para usar a conta da Lighter.")
    symbol = request.get("symbol", "BTC")
    if not isinstance(symbol, str) or not symbol or len(symbol) > 32 or not all(c.isascii() and (c.isalnum() or c in "_-") for c in symbol):
        raise BridgeError("Símbolo Lighter inválido.")
    if account < 0 or not 0 <= key_index <= 254:
        raise BridgeError("Índices de conta ou chave inválidos.")
    root = data_root() / "Lighter"
    root.mkdir(parents=True, exist_ok=True)
    path = root / (f"{network}-{account}.json" if symbol == "BTC" else f"{network}-{account}-{symbol}.json")
    if request["command"] == "check":
        return await connect(lighter, request, account, key_index, path)
    try:
        with account_lock(root / f"{network}-{account}.lock"):
            return await connect(lighter, request, account, key_index, path)
    except OSError as error:
        raise BridgeError("Não foi possível bloquear o diário da conta. Confira o armazenamento e outras instâncias.") from error


async def connect(sdk, request, account, key_index, path):
    client = sdk.SignerClient(NETWORKS[request["network"]], account, {key_index: request["key"]})

    async def finish_entry(result, actions):
        if result.get("action"):
            actions.append(result)
        if request["command"] == "rotate" and retryable_entry(result):
            try:
                retry = await execute(sdk, client, dict(request, only_open=True), account, key_index,
                                      path, continue_rotation=True)
            except Exception as error:
                return {"actions": actions, "position": None, "paused": True,
                        "reason": str(error) if isinstance(error, BridgeError) else type(error).__name__}
            if retry.get("action"):
                actions.append(retry)
            if retry.get("action") or retry.get("entry_skipped") or retry.get("risk_halt"):
                result = retry
        reason = entry_pause_reason(result)
        return {"actions": actions, "position": result["position"], "paused": bool(reason), "reason": reason}

    try:
        if client.check_client():
            raise BridgeError("A chave informada não corresponde à conta ou à rede da Lighter.")
        result = await execute(sdk, client, request, account, key_index, path)
        if request["command"] not in ("rotate", "risk"):
            return result
        risk_halt = result.get("risk_halt", False)
        closing = result.get("action", "").startswith("Fechar")
        if not closing:
            return await finish_entry(result, [])
        actions = [result]
        for _ in range(2):
            if Decimal(result["position"]) == 0:
                break
            try:
                result = await execute(sdk, client, request, account, key_index, path, continue_rotation=True)
            except Exception as error:
                return {"actions": actions, "position": None, "paused": True,
                        "close_pending": True,
                        "reason": str(error) if isinstance(error, BridgeError) else type(error).__name__}
            if result.get("action"):
                actions.append(result)
        if Decimal(result["position"]) != 0:
            return {"actions": actions, "position": result["position"], "paused": True,
                    "close_pending": True, "reason": CLOSE_PENDING}
        if risk_halt:
            return {"actions": actions, "position": result["position"], "paused": True, "reason": RISK_HALT}
        try:
            result = await execute(sdk, client, request, account, key_index, path, continue_rotation=True)
        except Exception as error:
            return {"actions": actions, "position": None, "paused": True,
                    "reason": str(error) if isinstance(error, BridgeError) else type(error).__name__}
        return await finish_entry(result, actions)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        request = json.load(sys.stdin)
        request["vault"] = Vault.open(data_root(), os.environ.get("EMA_TRADER_VAULT_PASSPHRASE"))
        print(json.dumps(asyncio.run(asyncio.wait_for(main(request), 120 if request.get("command") == "rotate" else 55))))
    except BridgeError as error:
        print(json.dumps({"error": str(error)}))
    except ModuleNotFoundError:
        print(json.dumps({"error": "Instale o SDK oficial com: py -3 -m pip install lighter-sdk==1.1.8"}))
    except Exception as error:
        print(json.dumps({"error": f"Falha na Lighter ({type(error).__name__}). Consulte a posição e o diário antes de retomar."}))
