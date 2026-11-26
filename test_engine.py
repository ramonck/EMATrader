import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import engine
from engine import Candle, Monitor, Signal, ema_scalping, take_signal


class EngineTests(unittest.TestCase):
    def test_grey_preserves_last_direction(self):
        prices = [100 - i for i in range(35)] + [66] * 10 + [66 + i * 3 for i in range(30)]
        candles = [Candle(i, p, p + 1, p - 1, p, 1) for i, p in enumerate(prices)]
        points = ema_scalping(candles)
        self.assertIn("AS", [p.action for p in points])
        self.assertIn("FS / AL", [p.action for p in points])
        self.assertTrue(any(p.band == 0 and p.side == -1 for p in points))
        for point in points:
            if not point.band:
                self.assertFalse(point.action)

    def test_reconnect_uses_last_missed_direction_once(self):
        newest = engine.now_ms()
        old = Signal(newest - 3 * engine.STEP, 101, 99, -1, -1, -1, -1, "FL / AS")
        reversal = Signal(newest - 2 * engine.STEP, 101, 99, 1, 1, 1, 1, "FS / AL")
        grey = Signal(newest, 101, 99, 0, 0, 0, 1, "")
        points = [old, reversal, grey]
        self.assertEqual(take_signal(points, 0), reversal)
        self.assertIsNone(take_signal(points, reversal.time))
        monitor = Monitor()
        monitor.managed = {"symbol": "BTC"}
        candles = [Candle(newest, 100, 101, 99, 100, 1)]
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EMA_TRADER_DATA_DIR": directory}):
            with patch("engine.candles_for", return_value=candles), patch("engine.ema_scalping", return_value=points):
                with patch("engine.protected_request", return_value={"actions": [], "paused": False}) as execute:
                    monitor.snapshot("SOL")
                    monitor.snapshot("SOL")
                    execute.assert_called_once()
                    self.assertEqual(execute.call_args.args[0]["symbol"], "BTC")
                    self.assertEqual(execute.call_args.kwargs["candle"], reversal.time)

    def test_shared_cache_only_loads_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "BTC.json"
            calls = []
            def load():
                calls.append(True)
                return [1, 2, 3]
            self.assertEqual(engine.shared_fetch(path, load, 30), [1, 2, 3])
            self.assertEqual(engine.shared_fetch(path, load, 30), [1, 2, 3])
            self.assertEqual(len(calls), 1)

    def test_retry_waits_for_fresh_data_and_a_cooldown(self):
        now = engine.now_ms()
        short = Signal(now - engine.STEP, 101, 99, -1, -1, -1, -1, "AS")
        grey = Signal(now, 101, 99, 0, 0, 0, -1, "")
        long = Signal(now + engine.STEP, 101, 99, 1, 1, 1, 1, "FS / AL")
        monitor = Monitor()
        monitor.managed = {"symbol": "BTC"}
        candle = Candle(now, 100, 101, 99, 100, 1)
        canceled = {"actions": [], "paused": False, "retry_entry": True}
        filled = {"actions": [], "paused": False, "retry_entry": False}
        with (tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EMA_TRADER_DATA_DIR": directory}),
              patch("engine.candles_for", return_value=[candle]),
              patch("engine.ema_scalping", side_effect=([short, grey], [short, grey], [short, grey], [short, grey, long])),
              patch("engine.protected_request", side_effect=(canceled, canceled, filled)) as dispatch,
              patch("engine.now_ms", return_value=now) as clock):
            monitor.snapshot("BTC")
            self.assertIs(monitor.entry_retry, short)
            monitor.snapshot("BTC")
            dispatch.assert_called_once()
            clock.return_value += engine.RETRY * 1000
            monitor.snapshot("BTC")
            self.assertTrue(dispatch.call_args.kwargs["retry_entry"])
            self.assertEqual(dispatch.call_args.kwargs["candle"], short.time)
            clock.return_value = long.time
            monitor.snapshot("BTC")
            self.assertFalse(dispatch.call_args.kwargs["retry_entry"])
            self.assertEqual(dispatch.call_args.kwargs["direction"], 1)
            self.assertIsNone(monitor.entry_retry)

    def test_btc_uses_lighter_and_caches_by_network(self):
        now = 1_800_000_000_000
        def get(url, query=None):
            network = "testnet" if "testnet" in url else "mainnet"
            self.assertTrue(url.startswith(engine.broker.NETWORKS[network]))
            market_id = 7 if network == "testnet" else 1
            price = 101 if network == "testnet" else 100
            if url.endswith("/orderBookDetails"):
                return {"order_book_details": [{"symbol": "BTC", "market_type": "perp", "status": "active",
                                                "market_id": market_id}]}
            self.assertTrue(url.endswith("/candles"))
            self.assertEqual(query["market_id"], market_id)
            return {"c": [{"t": t, "o": price, "h": price + 1, "l": price - 1, "c": price, "v": 2}
                          for t in (now - engine.STEP, now)]}

        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EMA_TRADER_DATA_DIR": directory}):
            old = Path(directory) / "quotes" / "BTC-15.json"
            engine.write(old, {"at": now / 1000, "data": [{"close": 9}]})
            with patch("engine.get", side_effect=get) as requests, patch("engine.now_ms", return_value=now):
                self.assertEqual([row.close for row in engine.candles_for("BTC")], [100])
                self.assertEqual([row.close for row in engine.candles_for("BTC", network="testnet")], [101])
                self.assertEqual([row.close for row in engine.candles_for("BTC")], [100])
                self.assertEqual(requests.call_count, 4)


if __name__ == "__main__":
    unittest.main()
