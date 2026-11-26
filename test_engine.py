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


if __name__ == "__main__":
    unittest.main()
