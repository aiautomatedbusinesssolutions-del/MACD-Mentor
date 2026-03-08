"""
Mentor Translator — Turns raw indicator values into 5th-grade-friendly
explanations with a stoplight signal system.
"""

import math
import pandas as pd


def detect_signal(df: pd.DataFrame) -> str:
    """
    Look at the most recent row of data and return a signal.

    Rules
    -----
    BULLISH  — MACD Line > Signal Line  AND  price > 200-day SMA
    BEARISH  — MACD Line < Signal Line  AND  price < 200-day SMA
    NEUTRAL  — anything else (mixed signals)

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: close, macd_line, signal_line, sma_200

    Returns
    -------
    str  — "BULLISH", "BEARISH", or "NEUTRAL"
    """
    latest = df.iloc[-1]

    macd = latest["macd_line"]
    signal = latest["signal_line"]
    price = latest["close"]
    sma = latest["sma_200"]

    # If the SMA hasn't had enough data to compute yet, we can't judge trend
    if math.isnan(sma):
        return "NEUTRAL"

    macd_bullish = macd > signal
    trend_bullish = price > sma

    if macd_bullish and trend_bullish:
        return "BULLISH"
    if (not macd_bullish) and (not trend_bullish):
        return "BEARISH"
    return "NEUTRAL"


def explain_signal(df: pd.DataFrame) -> dict:
    """
    Return a dict with the signal headline, color, and a plain-English
    "why" sentence based on the latest row of indicator data.

    Returns
    -------
    dict with keys: signal, headline, why, color
    """
    latest = df.iloc[-1]
    price = latest["close"]
    sma = latest["sma_200"]
    macd = latest["macd_line"]
    sig = latest["signal_line"]
    sma_valid = not math.isnan(sma)

    signal = detect_signal(df)

    # Build the "why" from the two components
    if sma_valid:
        trend_part = (
            f"Price (${price:,.2f}) is **above** the 200-day SMA (${sma:,.2f})"
            if price > sma
            else f"Price (${price:,.2f}) is **below** the 200-day SMA (${sma:,.2f})"
        )
    else:
        trend_part = "Not enough data yet to calculate the 200-day SMA"

    momentum_part = (
        "the MACD Line is above the Signal Line (momentum is rising)"
        if macd > sig
        else "the MACD Line is below the Signal Line (momentum is fading)"
    )

    why = f"{trend_part}, and {momentum_part}."

    if signal == "BULLISH":
        return {
            "signal": signal,
            "icon": "🟢",
            "label": "GO",
            "headline": "THE GREEN WAVE: GO",
            "why": why,
            "color": "green",
        }
    if signal == "BEARISH":
        return {
            "signal": signal,
            "icon": "🔴",
            "label": "STOP",
            "headline": "RED FLAG: STOP",
            "why": why,
            "color": "red",
        }
    return {
        "signal": signal,
        "icon": "🟡",
        "label": "CAUTION",
        "headline": "YELLOW LIGHT: CAUTION",
        "why": why,
        "color": "gray",
    }
