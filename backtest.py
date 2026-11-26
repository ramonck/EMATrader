"""Replay the 15-minute strategy against a local Binance Spot 5-minute CSV."""
import argparse
import csv
import json
import math
from datetime import datetime
from itertools import groupby
from pathlib import Path

from engine import STEP, Candle, ema_scalping

FIVE_MINUTES = STEP // 3


def utc_ms(text):
    timestamp = datetime.fromisoformat(text)
    if timestamp.utcoffset() is None:
        raise ValueError("Use an explicit time zone in --start and --end")
    return int(timestamp.timestamp() * 1000)


def candles_from_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        previous = None
        groups = groupby(csv.DictReader(file), lambda row: int(row["open_time_ms"]) // STEP)
        for number, group in groups:
            rows = list(group)
            start = number * STEP
            expected = [start + i * FIVE_MINUTES for i in range(3)]
            starts = [int(row["open_time_ms"]) for row in rows]
            if starts != expected or (previous is not None and start != previous):
                raise ValueError(f"Missing, duplicate or unordered candle near {start}")
            end = start + STEP
            yield Candle(end, float(rows[0]["open"]), max(float(row["high"]) for row in rows),
                         min(float(row["low"]) for row in rows), float(rows[-1]["close"]),
                         sum(float(row["volume"]) for row in rows))
            previous = end


def replay(candles, start, end, fee, margin_usd=None, leverage=1):
    if start >= end or start % STEP or end % STEP or not 0 <= fee < 1:
        raise ValueError("Provide aligned start/end times and a valid fee")
    if not candles or candles[0].time > start - 22 * STEP or candles[-1].time < end:
        raise ValueError("CSV must cover the requested window and its warm-up")
    if (margin_usd is not None and (not math.isfinite(margin_usd) or margin_usd <= 0)) or not 1 <= leverage <= 20:
        raise ValueError("Margin must be positive and leverage must be between 1 and 20")
    if leverage != 1 and margin_usd is None:
        raise ValueError("--leverage requires --margin-usd")
    signals = {point.time: point for point in ema_scalping(candles) if point.action}
    starting_value = margin_usd if margin_usd is not None else 1.0
    equity = high_water = starting_value
    drawdown = drawdown_cash = 0.0
    units = 0.0
    direction = 0
    entry_price = 0.0
    trades = wins = 0
    best = worst = None
    worst_unrealized = 0.0
    final_price = candles[-1].close
    first_price = None

    for candle in candles:
        bar_open = candle.time - STEP
        if not start <= bar_open < end:
            continue
        if first_price is None:
            first_price = candle.open
        signal = signals.get(bar_open)
        if signal and (margin_usd is not None or equity > 0):
            if direction:
                pnl = units * (direction * (candle.open - entry_price) - fee * (entry_price + candle.open))
                equity += pnl
                trades += 1
                wins += pnl > 0
                best = pnl if best is None else max(best, pnl)
                worst = pnl if worst is None else min(worst, pnl)
            order_margin = margin_usd if margin_usd is not None else max(equity, 0)
            direction = signal.side if order_margin else 0
            entry_price = candle.open
            units = order_margin * leverage / entry_price

        final_price = candle.close
        marked = equity + units * (direction * (final_price - entry_price) - fee * (entry_price + final_price))
        high_water = max(high_water, marked)
        drawdown = max(drawdown, 1 - marked / high_water)
        drawdown_cash = max(drawdown_cash, high_water - marked)
        adverse = candle.low if direction > 0 else candle.high
        worst_unrealized = min(worst_unrealized, units * (
            direction * (adverse - entry_price) - fee * (entry_price + adverse)))

    hold = final_price / first_price - 1 - fee * (1 + final_price / first_price)
    common = {"closed_trades": trades, "wins": wins, "open_side": direction}
    if margin_usd is not None:
        return dict(common, net_pnl_usd=round(marked - starting_value, 4),
                    closed_pnl_usd=round(equity - starting_value, 4), open_pnl_usd=round(marked - equity, 4),
                    avg_closed_margin_roi_pct=round((equity - starting_value) / trades / margin_usd * 100, 4) if trades else None,
                    max_peak_to_trough_usd=round(drawdown_cash, 4),
                    best_trade_usd=round(best, 4) if best is not None else None,
                    worst_trade_usd=round(worst, 4) if worst is not None else None,
                    worst_intrabar_trade_pnl_usd=round(worst_unrealized, 4))
    return dict(common, roi_pct=round((marked - 1) * 100, 4), closed_roi_pct=round((equity - 1) * 100, 4),
                max_drawdown_pct=round(drawdown * 100, 4), buy_hold_pct=round(hold * 100, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--start", required=True, type=utc_ms)
    parser.add_argument("--end", required=True, type=utc_ms)
    parser.add_argument("--fee-bps", type=float, default=1, help="assumed fee per side in basis points")
    parser.add_argument("--margin-usd", type=float, help="fixed USD margin per trade, with no reinvestment")
    parser.add_argument("--leverage", type=int, default=1)
    args = parser.parse_args()
    with_candles = list(candles_from_csv(args.csv))
    result = replay(with_candles, args.start, args.end, args.fee_bps / 10000, args.margin_usd, args.leverage)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
