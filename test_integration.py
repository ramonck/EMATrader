import asyncio
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace as Row
from unittest.mock import AsyncMock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import broker
from backtest import replay
from engine import STEP, Candle, Monitor, Signal
from i18n import tr
from knowledge import LANGUAGES, TOPICS, knowledge_rule
from local_mcp import LocalMCP


class AdoptionTests(unittest.TestCase):
    def test_adoption_reads_full_signed_position_without_trading(self):
        for sign in (-1, 1):
            with self.subTest(sign=sign), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "mainnet-1.json"
                market = Row(symbol="BTC", market_type="perp", status="active", market_id=1)
                position = Row(symbol="BTC", market_id=1, position="0.00123", sign=sign,
                               pending_order_count=0, avg_entry_price="60000", unrealized_pnl="1")
                client = Row(order_api=Row(
                    order_book_details=AsyncMock(return_value=Row(order_book_details=[market])),
                    account_active_orders=AsyncMock(return_value=Row(orders=[]))),
                    create_auth_token_with_expiry=lambda **_: ("token", None),
                    create_market_order=AsyncMock(), update_leverage=AsyncMock())
                request = {"command": "arm", "symbol": "BTC"}
                with patch("broker.account_snapshot", AsyncMock(return_value=Row(positions=[position]))):
                    result = asyncio.run(broker.execute(None, client, request, 1, 3, path))
                signed = Decimal("0.00123") * sign
                self.assertEqual(Decimal(result["position"]), signed)
                self.assertEqual(Decimal(json.loads(path.read_text())["position"]), signed)
                client.create_market_order.assert_not_awaited()
                client.update_leverage.assert_not_awaited()
                path.write_text('{"position":"0","candle":1,"pending":123}')
                with patch("broker.account_snapshot", AsyncMock(return_value=Row(positions=[position]))):
                    with self.assertRaises(broker.BridgeError):
                        asyncio.run(broker.execute(None, client, request, 1, 3, path))
                self.assertEqual(json.loads(path.read_text())["pending"], 123)

    def test_arm_waits_for_a_fresh_turn(self):
        monitor = Monitor()
        with patch("engine.protected_request", return_value={"positions": [{"symbol": "BTC", "sign": -1}]}) as request:
            with patch("engine.now_ms", return_value=123):
                config = {"symbol": "BTC", "network": "testnet", "account": 1}
                monitor.arm(config)
        request.assert_called_once_with(config, command="arm")
        self.assertEqual(monitor.cursor, 123)
        self.assertEqual(monitor.position_rows[0]["sign"], -1)

    def test_reverse_signal_closes_full_adopted_short_reduce_only(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "Lighter"
            journal.mkdir()
            path = journal / "mainnet-1.json"
            path.write_text('{"position":"-0.00123","candle":1}')
            market = Row(symbol="BTC", market_type="perp", status="active", market_id=1,
                         size_decimals=5, price_decimals=2)
            row = Row(market_id=1, position="0.00123", sign=-1)
            receipt = Row(filled_base_amount="0.00123", filled_quote_amount="73.8",
                          status="filled", updated_at=3)
            send = AsyncMock(return_value=(None, Row(code=200, tx_hash="test"), None))
            client = Row(order_api=Row(
                order_book_details=AsyncMock(return_value=Row(order_book_details=[market])),
                account_active_orders=AsyncMock(return_value=Row(orders=[])),
                account_inactive_orders=AsyncMock(side_effect=lambda *_: Row(orders=[
                    Row(**vars(receipt), client_order_index=send.await_args.args[1])]))),
                create_auth_token_with_expiry=lambda **_: ("token", None),
                create_market_order=send)
            request = {"command": "rotate", "symbol": "BTC", "direction": 1, "candle": 2,
                       "margin": "100", "leverage": 5, "network": "mainnet"}
            with (patch("broker.account_snapshot", AsyncMock(return_value=Row(positions=[row]))),
                  patch("broker.position", AsyncMock(return_value=(Decimal(0), None))),
                  patch("broker.execution_quote", AsyncMock(return_value=Decimal(60000))),
                  patch("broker.market_depth_price", AsyncMock(return_value=Decimal(60000))),
                  patch("broker.asyncio.sleep", AsyncMock())):
                result = asyncio.run(broker.execute(None, client, request, 1, 3, path))
            args = send.await_args.args
            self.assertEqual(args[2], 123)
            self.assertFalse(args[4])
            self.assertTrue(send.await_args.kwargs["reduce_only"])
            self.assertEqual(result["position"], "0")
            self.assertEqual(result["action"], "Fechar short")


class KnowledgeAndMCPTests(unittest.TestCase):
    def test_index_matches_topics_in_all_languages(self):
        for language in LANGUAGES:
            index = knowledge_rule(language, "index")
            for topic in TOPICS:
                self.assertIn(f"({topic}.md)", index)
                self.assertTrue(knowledge_rule(language, topic).startswith(f"# {topic}"))

    def test_local_protocol_auth_and_data_bounds(self):
        service = LocalMCP()
        url = service.start(0)
        monitor = Monitor()
        monitor.managed = {"symbol": "BTC", "key": "private-key-never-published"}
        candle = Candle(100, 1, 1.2, 0.8, 1.1, 2)
        monitor.market_state = {"BTC": ([candle], Signal(100, 1.02, 0.98, 0, 0, 1, 1, "AL"))}
        service.publish(monitor, "SOL")

        def query(method, params=None, authenticated=True, origin=None):
            headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
            if authenticated:
                headers["Authorization"] = "Bearer " + service.token
            if origin:
                headers["Origin"] = origin
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
            with urlopen(Request(url, body, headers), timeout=4) as response:
                return json.load(response)

        try:
            for auth, origin, code in ((False, None, 401), (True, "https://example.invalid", 403)):
                with self.assertRaises(HTTPError) as error:
                    query("tools/list", authenticated=auth, origin=origin)
                self.assertEqual(error.exception.code, code)
                error.exception.close()
            self.assertEqual(query("initialize", {"protocolVersion": "2025-06-18"})["result"]["protocolVersion"], "2025-06-18")
            self.assertEqual(len(query("tools/list")["result"]["tools"]), 4)
            status = query("tools/call", {"name": "status"})["result"]["content"][0]["text"]
            self.assertEqual(json.loads(status)["managed_asset"], "BTC")
            self.assertEqual(json.loads(status)["markets"]["BTC"]["range"], [0.8, 1.2])
            self.assertLess(len(status), 700)
            self.assertNotIn("private-key", status)
            candles = query("tools/call", {"name": "candles", "arguments": {"symbol": "BTC", "limit": 1}})
            self.assertEqual(len(json.loads(candles["result"]["content"][0]["text"])), 1)
            self.assertIn("error", query("tools/call", {"name": "candles", "arguments": {"limit": 25}}))
            self.assertIn("error", query("tools/call", {"name": "place_order"}))
        finally:
            service.stop()

    def test_order_status_is_available_in_all_languages(self):
        message = "Ordens automáticas ativas para {symbol}"
        expected = ("Ordens automáticas ativas para BTC", "Automatic orders enabled for BTC",
                    "Órdenes automáticas activas para BTC")
        self.assertEqual(tuple(tr(language, message, symbol="BTC") for language in LANGUAGES), expected)


class BacktestTests(unittest.TestCase):
    def test_fixed_margin_tracks_closed_and_open_pnl_separately(self):
        start = 24 * STEP
        candles = [Candle(i * STEP, 100, 100, 100, 100, 10) for i in range(1, 25)]
        candles.extend((Candle(start + STEP, 100, 110, 100, 110, 10),
                        Candle(start + 2 * STEP, 110, 110, 99, 99, 10)))
        signals = [Signal(start, 1, 1, 0, 0, 1, 1, "AL"),
                   Signal(start + STEP, 1, 1, 0, 0, -1, -1, "FL / AS")]
        with patch("backtest.ema_scalping", return_value=signals):
            result = replay(candles, start, start + 2 * STEP, 0, 100, 10)
        self.assertEqual(result["closed_trades"], 1)
        self.assertEqual(result["closed_pnl_usd"], 100)
        self.assertEqual(result["open_pnl_usd"], 100)
        self.assertEqual(result["net_pnl_usd"], 200)
        self.assertEqual(result["avg_closed_margin_roi_pct"], 100)
