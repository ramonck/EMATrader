"""Replay the 15-minute strategy against a local OHLCV CSV."""
import argparse
import csv
import json
import math
from datetime import datetime
from itertools import groupby
from pathlib import Path

from engine import STEP, Candle, ema_scalping
from broker import next_margin


def utc_ms(text):
    timestamp = datetime.fromisoformat(text)
    if timestamp.utcoffset() is None:
        raise ValueError("Use an explicit time zone in --start and --end")
    return int(timestamp.timestamp() * 1000)


def candles_from_csv(path, input_minutes=5):
    interval = input_minutes * 60_000
    if input_minutes not in (5, 15):
        raise ValueError("CSV interval must be 5 or 15 minutes")
    with path.open(encoding="utf-8-sig", newline="") as file:
        previous = None
        groups = groupby(csv.DictReader(file), lambda row: int(row["open_time_ms"]) // STEP)
        for number, group in groups:
            rows = list(group)
            start = number * STEP
            expected = list(range(start, start + STEP, interval))
            starts = [int(row["open_time_ms"]) for row in rows]
            if starts != expected or (previous is not None and start != previous):
                raise ValueError(f"Missing, duplicate or unordered candle near {start}")
            end = start + STEP
            yield Candle(end, float(rows[0]["open"]), max(float(row["high"]) for row in rows),
                         min(float(row["low"]) for row in rows), float(rows[-1]["close"]),
                         sum(float(row["volume"]) for row in rows))
            previous = end


def replay(candles, start, end, fee, margin_usd=None, leverage=1, compound=False, stop_loss=0, max_account_drawdown=0,
           confirmation_bars=1, require_market_close=False, trend_confirm_short_exit=False):
    if start >= end or start % STEP or end % STEP or not 0 <= fee < 1:
        raise ValueError("Provide aligned start/end times and a valid fee")
    if not candles or candles[0].time > start - 22 * STEP or candles[-1].time < end:
        raise ValueError("CSV must cover the requested window and its warm-up")
    if (margin_usd is not None and (not math.isfinite(margin_usd) or margin_usd <= 0)) or not 1 <= leverage <= 20:
        raise ValueError("Margin must be positive and leverage must be between 1 and 20")
    if leverage != 1 and margin_usd is None:
        raise ValueError("--leverage requires --margin-usd")
    if compound and margin_usd is None:
        raise ValueError("--compound requires --margin-usd")
    if not 0 <= stop_loss < 1:
        raise ValueError("Stop loss must be between 0% and 100% of margin")
    if not 0 <= max_account_drawdown < 1:
        raise ValueError("Account drawdown must be between 0% and 100%")
    if trend_confirm_short_exit and (confirmation_bars != 1 or require_market_close):
        raise ValueError("Run the short-exit trend filter separately from other experiments")
    points = ema_scalping(candles, confirmation_bars, require_market_close,
                          trend_confirm_short_exit=trend_confirm_short_exit)
    signals = {point.time: point for point in points if point.action}
    starting_value = margin_usd if margin_usd is not None else 1.0
    equity = high_water = starting_value
    order_margin = target_margin = starting_value
    drawdown = drawdown_cash = 0.0
    units = 0.0
    direction = 0
    entry_price = 0.0
    trades = wins = 0
    best = worst = None
    stops = 0
    halt_signal = None
    worst_unrealized = 0.0
    final_price = candles[-1].close
    first_price = None

    def settle(price):
        nonlocal equity, target_margin, trades, wins, best, worst, units, direction
        pnl = units * (direction * (price - entry_price) - fee * (entry_price + price))
        equity += pnl
        if compound:
            target_margin = next_margin(margin_usd, order_margin, pnl)
        trades += 1
        wins += pnl > 0
        best = pnl if best is None else max(best, pnl)
        worst = pnl if worst is None else min(worst, pnl)
        units = direction = 0

    for candle in candles:
        bar_open = candle.time - STEP
        if not start <= bar_open < end:
            continue
        if first_price is None:
            first_price = candle.open
        signal = signals.get(bar_open) if halt_signal is None else None
        if halt_signal is not None and direction:
            settle(candle.open)
        stop_price = entry_price * (1 - direction * stop_loss / leverage)
        gap_stop = stop_loss and direction and direction * (candle.open - stop_price) <= 0
        if gap_stop:
            settle(candle.open)
            stops += 1
        if signal and not gap_stop and (direction or equity > 0 or (margin_usd is not None and not compound)):
            if direction:
                settle(candle.open)
            if compound:
                order_margin = min(target_margin, max(equity, 0))
            else:
                order_margin = margin_usd if margin_usd is not None else max(equity, 0)
            direction = signal.side if order_margin else 0
            entry_price = candle.open
            units = order_margin * leverage / entry_price

        final_price = candle.close
        adverse = candle.low if direction > 0 else candle.high
        stop_price = entry_price * (1 - direction * stop_loss / leverage)
        if stop_loss and direction and direction * (adverse - stop_price) <= 0:
            settle(stop_price)
            stops += 1
        marked = equity + units * (direction * (final_price - entry_price) - fee * (entry_price + final_price))
        high_water = max(high_water, marked)
        drawdown = max(drawdown, 1 - marked / high_water)
        if max_account_drawdown and drawdown >= max_account_drawdown and halt_signal is None:
            halt_signal = candle.time
        drawdown_cash = max(drawdown_cash, high_water - marked)
        worst_unrealized = min(worst_unrealized, units * (
            direction * (adverse - entry_price) - fee * (entry_price + adverse)))

    hold = final_price / first_price - 1 - fee * (1 + final_price / first_price)
    common = {"closed_trades": trades, "wins": wins, "open_side": direction}
    if stop_loss:
        common["stop_exits"] = stops
    if max_account_drawdown:
        common["account_halt_signal_ms"] = halt_signal
    if margin_usd is not None:
        result = dict(common, net_pnl_usd=round(marked - starting_value, 4),
                    closed_pnl_usd=round(equity - starting_value, 4), open_pnl_usd=round(marked - equity, 4),
                    avg_closed_margin_roi_pct=round((equity - starting_value) / trades / margin_usd * 100, 4) if trades else None,
                    max_peak_to_trough_usd=round(drawdown_cash, 4),
                    best_trade_usd=round(best, 4) if best is not None else None,
                    worst_trade_usd=round(worst, 4) if worst is not None else None,
                    worst_intrabar_trade_pnl_usd=round(worst_unrealized, 4))
        if compound:
            result.update(ending_equity_usd=round(marked, 4),
                          max_drawdown_pct=round(drawdown * 100, 4),
                          roi_pct=round((marked / starting_value - 1) * 100, 4))
            result.pop("avg_closed_margin_roi_pct")
        return result
    return dict(common, roi_pct=round((marked - 1) * 100, 4), closed_roi_pct=round((equity - 1) * 100, 4),
                max_drawdown_pct=round(drawdown * 100, 4), buy_hold_pct=round(hold * 100, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--input-minutes", type=int, choices=(5, 15), default=5, help="interval in the OHLCV CSV")
    parser.add_argument("--start", required=True, type=utc_ms)
    parser.add_argument("--end", required=True, type=utc_ms)
    parser.add_argument("--fee-bps", type=float, default=1, help="assumed fee per side in basis points")
    parser.add_argument("--margin-usd", type=float, help="USD margin per trade, or starting margin with --compound")
    parser.add_argument("--leverage", type=int, default=1)
    parser.add_argument("--compound", action="store_true", help="reinvest wins, reset to base after losses, limited by equity")
    parser.add_argument("--stop-loss", type=float, default=0, help="stop loss as a percent of margin, before fees")
    parser.add_argument("--max-account-drawdown", type=float, default=0,
                        help="percent drawdown from peak equity that closes next bar and halts trading")
    parser.add_argument("--confirmation-bars", type=int, choices=(1, 2), default=1,
                        help="consecutive same-color closed EMA bars before a reversal")
    parser.add_argument("--require-market-close", action="store_true",
                        help="require the raw OHLC close outside the EMA band in the same direction")
    parser.add_argument("--trend-confirm-short-exit", action="store_true",
                        help="on short-to-long turns, require hourly long bias and a bullish raw close above the 15m band")
    args = parser.parse_args()
    with_candles = list(candles_from_csv(args.csv, args.input_minutes))
    result = replay(with_candles, args.start, args.end, args.fee_bps / 10000,
                    args.margin_usd, args.leverage, args.compound, args.stop_loss / 100, args.max_account_drawdown / 100,
                    confirmation_bars=args.confirmation_bars, require_market_close=args.require_market_close,
                    trend_confirm_short_exit=args.trend_confirm_short_exit)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
