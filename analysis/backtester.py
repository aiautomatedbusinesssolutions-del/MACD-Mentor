"""
Backtester — Historical Pattern Matcher.

Scans 5 years of daily data to find every day whose trend/momentum
alignment exactly matches today's, then measures what happened to
the price 30 trading days later.
"""

import math
import pandas as pd


def _setup_key(row: pd.Series) -> str | None:
    """
    Return a fine-grained setup key for a single row.

    Four possible states based on two binary conditions:
        price vs 200-day SMA  x  MACD vs Signal Line

    Returns None if the SMA hasn't computed yet (not enough history).
    """
    sma = row["sma_200"]
    if math.isnan(sma):
        return None

    trend_up = row["close"] > sma
    momentum_up = row["macd_line"] > row["signal_line"]

    if trend_up and momentum_up:
        return "BULLISH"
    if (not trend_up) and (not momentum_up):
        return "BEARISH"
    if trend_up and (not momentum_up):
        return "NEUTRAL_TREND_UP"
    return "NEUTRAL_TREND_DOWN"


def _signal_to_key(signal: str, df: pd.DataFrame) -> str | None:
    """
    Map the current signal to the matching setup key.

    For BULLISH / BEARISH the key is the same as the signal name.
    For NEUTRAL we look at the latest row to determine which flavour.
    """
    if signal in ("BULLISH", "BEARISH"):
        return signal
    # NEUTRAL — figure out the exact sub-type from today's data
    return _setup_key(df.iloc[-1])


def pattern_match_30d(df: pd.DataFrame, current_signal: str) -> dict | None:
    """
    Find every historical day whose setup key matches today's,
    measure the 30-trading-day forward return, and summarize.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain: close, macd_line, signal_line, sma_200, date.
        Sorted ascending by date.
    current_signal : str
        "BULLISH", "BEARISH", or "NEUTRAL".

    Returns
    -------
    dict with keys: matches, win_pct, avg_return, small_sample, recent
        recent is a list of dicts (up to 10 most recent) with:
            date, entry_price, price_30d, pct_change
    None only if the SMA hasn't computed for today's row.
    """
    target_key = _signal_to_key(current_signal, df)
    if target_key is None:
        return None

    all_matches = []

    # Only check rows where there are at least 30 days of future data
    for i in range(len(df) - 30):
        row = df.iloc[i]
        if _setup_key(row) != target_key:
            continue

        price_now = row["close"]
        price_30d = df.iloc[i + 30]["close"]
        pct_change = (price_30d - price_now) / price_now * 100

        all_matches.append({
            "date": row["date"],
            "entry_price": round(price_now, 2),
            "price_30d": round(price_30d, 2),
            "pct_change": round(pct_change, 2),
        })

    if not all_matches:
        return None

    returns = [m["pct_change"] for m in all_matches]
    total = len(returns)
    wins = sum(1 for r in returns if r > 0)

    return {
        "matches": total,
        "win_pct": round(wins / total * 100, 1),
        "avg_return": round(sum(returns) / total, 2),
        "small_sample": total < 3,
        "recent": all_matches[-10:],  # 10 most recent (list is chronological)
    }
