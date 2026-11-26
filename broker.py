"""Lighter execution, account-wide locking and reconciled order journal."""
import asyncio
import json
import os
import sys
import time
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
from storage import account_lock, data_root, write

NETWORKS = {
    "testnet": "https://testnet.zklighter.elliot.ai",
    "mainnet": "https://mainnet.zklighter.elliot.ai",
}


class BridgeError(Exception):
    pass


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


async def ensure_account_flat(sdk, client, account, auth, state_path):
    snapshot = await account_snapshot(sdk, client, account)
    if any(Decimal(row.position) != 0 for row in snapshot.positions):
        raise BridgeError("A conta já tem posição aberta. Novas entradas estão bloqueadas.")
    active = await client.order_api.account_active_orders(auth, account)
    if active.orders or snapshot.pending_order_count:
        raise BridgeError("Há ordens ativas ou pendentes na conta. Novas entradas estão bloqueadas.")
    prefix = state_path.stem.split("-", 2)[:2]
    for journal in state_path.parent.glob("-".join(prefix) + "*.json"):
        name = journal.stem.split("-", 2)
        if name[:2] == prefix and json.loads(journal.read_text(encoding="utf-8")).get("pending"):
            raise BridgeError("Há uma execução pendente no diário desta conta.")


def save_state(path, state):
    write(path, state)


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
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"position": "0", "candle": -1}
    if command == "check":
        blocked = None
        if request.get("single_position") and not current:
            try:
                await ensure_account_flat(sdk, client, account, auth, state_path)
            except BridgeError as error:
                blocked = str(error)
        return {"position": str(current), "market": market_id, "breakout_filter": True, "entry_room_filter": True,
                "pending": bool(state.get("pending")), "blocked": blocked, "positions": public_positions(snapshot),
                "ready": not state.get("pending") and Decimal(state["position"]) == current}
    if command == "adopt":
        expected = Decimal(str(request["expected_position"]))
        if state.get("pending"):
            raise BridgeError("O diário tem uma ordem pendente para este mercado. Concilie antes de assumir a posição.")
        if not current or expected != current:
            raise BridgeError("A posição mudou. Confira a nova quantidade antes de assumir.")
        active = await client.order_api.account_active_orders(auth, account, market_id)
        if active.orders or (config is not None and config.pending_order_count):
            raise BridgeError("Há ordem ativa ou pendente neste mercado. Confira antes de assumir.")
        save_state(state_path, dict(state, position=str(current), adopted_at=int(time.time() * 1000)))
        return {"ready": True, "position": str(current), "market": market_id, "positions": public_positions(snapshot)}
    if state.get("pending") or Decimal(state["position"]) != current:
        raise BridgeError("Estado da posição divergente ou ordem pendente. Confira a conta e o diário antes de retomar.")
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
        return {"position": "0", **({"entry_skipped": "Binance"} if request.get("entry_signal") else {})}
    if current and request.get("only_open", False):
        return {"position": str(current)}
    active = await client.order_api.account_active_orders(auth, account, market_id)
    if active.orders:
        raise BridgeError(f"Há ordens {symbol} abertas na conta selecionada.")

    margin = Decimal(str(request["margin"]))
    leverage = int(request["leverage"])
    book_price = request["command"] == "rotate" and "slippage" not in request
    slippage = Decimal(str(request.get("slippage", 0))) / 100
    if not (0 < margin <= 1000000 and 1 <= leverage <= 20 and
            (book_price or 0 < slippage <= Decimal("0.05"))):
        raise BridgeError("Margem, alavancagem ou desvio de preço inválido.")
    closing = current != 0
    selling = current > 0 if closing else target < 0
    entry_levels = None
    if not closing and "prior_high" in request:
        entry_levels = (Decimal(str(request["prior_low"])), Decimal(str(request["prior_high"])))
    quote = await execution_quote(client, market_id, selling, entry_levels)
    if quote is None:
        return {"position": "0", "entry_skipped": "livro Lighter"}
    if not closing:
        if command == "rotate":
            await ensure_account_flat(sdk, client, account, auth, state_path)
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
        await ensure_account_flat(sdk, client, account, auth, state_path)
    bound = (market_limit if book_price else quote * (1 - slippage if selling else 1 + slippage)) * price_scale
    limit = int(bound.to_integral_value(rounding=ROUND_CEILING if selling else ROUND_FLOOR))
    order_index = max(time.time_ns() // 1_000_000, int(state.get("last", {}).get("order", 0)) + 1)
    action = ("Fechar long" if current > 0 else "Fechar short") if closing else ("Abrir short" if selling else "Abrir long")
    save_state(state_path, {"position": str(current), "candle": candle, "pending": order_index, "action": action})
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
        after, _ = await position(sdk, client, account, market_id)
        if after != expected:
            continue
        report = {"position": str(after), "action": action, "filled": str(filled), "order": str(order_index),
                  "price": str(Decimal(order.filled_quote_amount) / filled) if filled else "0",
                  "status": order.status, "hash": sent.tx_hash, "time": order.updated_at,
                  "partial": filled < Decimal(amount) / size_scale}
        audit = dict(report, network=request["network"], candle=candle, trigger=request.get("trigger"), margin_usd=str(margin),
                     leverage=leverage, account=account, symbol=symbol)
        with (state_path.parent.parent / "operacoes-lighter.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps(audit) + "\n")
            file.flush()
            os.fsync(file.fileno())
        save_state(state_path, {"position": str(after), "candle": candle, "last": report})
        return report
    raise BridgeError("Execução não conciliada. O diário bloqueou outros envios até revisão da ordem.")


async def main(request):
    import lighter
    account = int(request["account"])
    key_index = int(request["key_index"])
    network = request["network"]
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
    try:
        if client.check_client():
            raise BridgeError("A chave informada não corresponde à conta ou à rede da Lighter.")
        result = await execute(sdk, client, request, account, key_index, path)
        if request["command"] != "rotate":
            return result
        actions = [result] if result.get("action") else []
        closing = result.get("action", "").startswith("Fechar")
        if not closing:
            return {"actions": actions, "position": result["position"],
                    "paused": bool(result.get("partial") or result.get("entry_skipped"))}
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
            return {"actions": actions, "position": result["position"], "paused": True, "close_pending": True}
        try:
            result = await execute(sdk, client, request, account, key_index, path, continue_rotation=True)
        except Exception as error:
            return {"actions": actions, "position": None, "paused": True,
                    "reason": str(error) if isinstance(error, BridgeError) else type(error).__name__}
        if result.get("action"):
            actions.append(result)
        return {"actions": actions, "position": result["position"],
                "paused": bool(result.get("partial") or result.get("entry_skipped"))}
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        request = json.load(sys.stdin)
        print(json.dumps(asyncio.run(asyncio.wait_for(main(request), 120 if request.get("command") == "rotate" else 55))))
    except BridgeError as error:
        print(json.dumps({"error": str(error)}))
    except ModuleNotFoundError:
        print(json.dumps({"error": "Instale o SDK oficial com: py -3 -m pip install lighter-sdk==1.1.8"}))
    except Exception as error:
        print(json.dumps({"error": f"Falha na Lighter ({type(error).__name__}). Consulte a posição e o diário antes de retomar."}))
