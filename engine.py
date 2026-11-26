"""Market data and the shared 15-minute EMA strategy."""

import asyncio
import json
import re
import time
from dataclasses import asdict, dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import broker
from storage import account_lock, data_root, read, write

STEP = 900_000
RETRY = 120
NORMAL_REFRESH = 300


def get(url, query=None):
    headers = {"User-Agent": "EMA-Trader/1.0"}
    request = Request(url + ("?" + urlencode(query) if query else ""), headers=headers)
    max_bytes = 8 * 1024 * 1024
    with urlopen(request, timeout=15) as response:
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("A resposta excedeu o tamanho esperado.")
    data = json.loads(body)
    if isinstance(data, dict) and data.get("code", 200) != 200:
        raise ValueError(data.get("message", "A consulta foi rejeitada."))
    return data


def now_ms():
    return time.time_ns() // 1_000_000


def symbol_key(symbol):
    if not re.fullmatch(r"[A-Z0-9_-]{1,32}", symbol):
        raise ValueError("Símbolo inválido.")
    return symbol


def shared_fetch(path, loader, lifetime):
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 16
    while True:
        cached = read(path, {})
        if time.time() - cached.get("at", 0) < lifetime:
            return cached["data"]
        lock = account_lock(path.with_suffix(".lock"))
        try:
            lock.__enter__()
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.15)
            continue
        try:
            cached = read(path, {})
            if time.time() - cached.get("at", 0) < lifetime:
                return cached["data"]
            data = loader()
            write(path, {"at": time.time(), "data": data})
            return data
        finally:
            lock.__exit__(None, None, None)


def markets(network="mainnet"):
    name = "catalog.json" if network == "mainnet" else f"catalog-{network}.json"
    path = data_root() / name
    cached = read(path, {})

    def load():
        return get(broker.NETWORKS[network] + "/api/v1/orderBookDetails")["order_book_details"]

    try:
        items = shared_fetch(path, load, 7 * 86400 if cached.get("data") else RETRY)
    except (OSError, ValueError):
        items = cached.get("data", [])
    return {row["symbol"]: row["market_id"] for row in items
            if row["market_type"] == "perp" and row["status"] == "active"
            and re.fullmatch(r"[A-Z0-9_-]{1,32}", row["symbol"])}


@dataclass(frozen=True)
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    time: int
    upper: float
    lower: float
    upper_change: float
    lower_change: float
    band: int
    side: int
    action: str


def ema_scalping(candles):
    points = []
    bands = []
    side = 0
    previous_open = previous_close = None
    upper = lower = None
    for candle in candles:
        close = (candle.open + candle.high + candle.low + candle.close) / 4
        opening = (candle.open + candle.close) / 2 if previous_open is None else (previous_open + previous_close) / 2
        previous_open, previous_close = opening, close
        high, low = max(candle.high, opening, close), min(candle.low, opening, close)
        upper = high if upper is None else upper + (high - upper) / 11
        lower = low if lower is None else lower + (low - lower) / 11
        bands.append((upper, lower))
        if len(bands) <= 22:
            continue
        up, down = upper - bands[-23][0], lower - bands[-23][1]
        band = 1 if close > upper and up > 0 and down > 0 else -1 if close < lower and up < 0 and down < 0 else 0
        action = ""
        if band and band != side:
            action = ("FS / AL" if side < 0 else "AL") if band > 0 else ("FL / AS" if side > 0 else "AS")
            side = band
        points.append(Signal(candle.time, upper, lower, up, down, band, side, action))
    return points


def candles_for(symbol, interval=15, network="mainnet"):
    symbol_key(symbol)
    close_step = interval * 60_000
    path = data_root() / "quotes" / f"lighter-{network}-{symbol}-{interval}.json"

    def load():
        limit = now_ms()
        market_id = markets(network).get(symbol)
        if market_id is None:
            raise ValueError(f"{symbol}: mercado indisponível no catálogo da Lighter.")
        response = get(broker.NETWORKS[network] + "/api/v1/candles", {
            "market_id": market_id, "resolution": f"{interval}m", "count_back": 500,
            "start_timestamp": limit - 500 * close_step, "end_timestamp": limit, "set_timestamp_to_end": "false",
        })
        ready = {}
        for row in response["c"]:
            stamp = int(row["t"])
            end = (stamp * 1000 if stamp < 100_000_000_000 else stamp) + close_step
            prices = [float(row.get(key, 0)) for key in ("o", "h", "l", "c")]
            if end <= limit and min(prices) > 0 and prices[1] >= max(prices[0], prices[3]) and prices[2] <= min(prices[0], prices[3]):
                ready[end] = asdict(Candle(end, *prices, float(row.get("v", 0))))
        return [ready[stamp] for stamp in sorted(ready)]

    data = shared_fetch(path, load, 15)
    return [Candle(**row) for row in data]


def account_positions(network, index):
    data = get(broker.NETWORKS[network] + "/api/v1/account",
               {"by": "index", "value": index, "active_only": "true"})
    account = next(row for row in data["accounts"] if int(row["index"]) == index)
    fields = ("symbol", "position", "sign", "avg_entry_price", "unrealized_pnl")
    return [{field: row[field] for field in fields} for row in account["positions"] if float(row["position"])]


def protected_request(config, **changes):
    return asyncio.run(asyncio.wait_for(broker.main({**config, **changes}), timeout=120))


def take_signal(points, cursor):
    """After an outage, use the latest confirmed rotation. Grey preserves its direction."""
    return next((point for point in reversed(points) if point.time > cursor and point.action), None)


class Monitor:
    def __init__(self):
        self.managed = None
        self.cursor = 0
        self.account = None
        self.position_rows = []
        self.closed_at = 0
        self.last_action = None
        self.return_at = 0
        self.trade_error = ""
        self.entry_retry = None
        self.entry_retry_at = 0
        self.market_state = {}
        self.market_state_network = None

    @property
    def market_network(self):
        return self.account[0] if self.account else "mainnet"

    def arm(self, config, on_ready=None):
        fields = ("network", "account", "symbol")
        if self.managed and any(config[field] != self.managed[field] for field in fields):
            raise ValueError("Desative a automação atual antes de trocar de conta, rede ou ativo.")
        result = protected_request(config, command="arm")
        if on_ready is not None:
            on_ready()
        self.managed = config.copy()
        self.account = config["network"], config["account"]
        self.position_rows = result.get("positions", [])
        self.closed_at = now_ms()
        self.cursor = now_ms()
        self.trade_error = ""
        self.entry_retry = None

    def snapshot(self, selected):
        self.last_action = None
        errors = []
        managed = self.managed
        network = self.market_network
        if network != self.market_state_network:
            self.market_state = {}
            self.market_state_network = network
        watched = {selected} | ({managed["symbol"]} if managed else set())
        results = {}
        for symbol in watched:
            try:
                candles = candles_for(symbol, network=network)
                points = ema_scalping(candles)
                if not points or now_ms() - points[-1].time > 2 * STEP:
                    raise ValueError("Candles fechados desatualizados.")
                results[symbol] = candles, points
            except (OSError, ValueError) as error:
                errors.append(f"{symbol}: {error}")
        self.market_state = {symbol: data for symbol, data in self.market_state.items() if symbol in watched}
        self.market_state.update({symbol: (candles[-24:], points[-1])
                                  for symbol, (candles, points) in results.items()})
        orders = []
        if managed:
            points = results.get(managed["symbol"], (None, []))[1]
            signal = take_signal(points, self.cursor)
            if signal or (points and self.entry_retry and points[-1].side != self.entry_retry.side):
                self.entry_retry = None
            if not signal and points and self.entry_retry and now_ms() >= self.entry_retry_at:
                signal = self.entry_retry
            if signal or managed.get("drawdown"):
                try:
                    if signal:
                        result = protected_request(managed, command="rotate", candle=signal.time,
                                                   direction=signal.side, trigger="EMA 15m",
                                                   retry_entry=(signal is self.entry_retry))
                        self.cursor = signal.time
                        self.entry_retry = signal if result.get("retry_entry") else None
                        if self.entry_retry:
                            self.entry_retry_at = now_ms() + RETRY * 1000
                    else:
                        result = protected_request(managed, command="risk")
                    orders = result["actions"]
                    if result["paused"]:
                        self.managed = None
                        self.entry_retry = None
                        self.trade_error = result.get("reason") or "Execução pausada. Confira posição e diário."
                except Exception as error:
                    self.managed = None
                    self.entry_retry = None
                    self.trade_error = str(error)
        if self.account:
            try:
                self.position_rows = account_positions(*self.account)
                self.closed_at = now_ms()
            except (OSError, ValueError, StopIteration) as error:
                errors.append(f"Conta: {error}")
        if selected in results:
            candles, points = results[selected]
            latest = points[-1]
            self.last_action = latest
            path = data_root() / "history" / f"lighter-{network}-{selected}.json"
            record = {"at": now_ms(), "close": candles[-1].close, "signal": asdict(latest)}
            write(path, record)
        else:
            candles, points = [], []
        return candles, points, orders, errors
