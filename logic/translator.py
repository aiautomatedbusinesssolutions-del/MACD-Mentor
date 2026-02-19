"""
Mentor Translator — Turns raw indicator values into 5th-grade-friendly
explanations and a "Chart School" candlestick lesson.
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


def explain_macd(macd_line: float, signal_line: float, histogram: float) -> str:
    """
    Return a plain-English 'Mentor Box' explanation of the current MACD state.
    """
    if macd_line > signal_line and histogram > 0:
        return (
            "🟢 **Bullish Signal!** "
            "The MACD line just crossed ABOVE the Signal line. "
            "Think of it like a race — the fast runner (MACD) just passed "
            "the slow runner (Signal). That usually means prices are "
            "picking up speed to go UP."
        )
    if macd_line < signal_line and histogram < 0:
        return (
            "🔴 **Bearish Signal!** "
            "The MACD line crossed BELOW the Signal line. "
            "The fast runner fell behind — prices might be slowing down "
            "or heading lower."
        )
    return (
        "🟡 **Neutral — Wait and Watch.** "
        "The MACD and Signal lines are close together. "
        "Neither team is winning yet, so there's no clear direction."
    )


def explain_sma(price: float, sma_200: float) -> str:
    """
    Explain where the price sits relative to the 200-day SMA.
    """
    if sma_200 is None or price is None:
        return "Not enough data yet to calculate the 200-day average."

    if price > sma_200:
        pct = ((price - sma_200) / sma_200) * 100
        return (
            f"📈 The price (${price:,.2f}) is **above** the 200-day average "
            f"(${sma_200:,.2f}) by {pct:.1f}%. "
            "That's like a student scoring above the class average all semester — "
            "a sign of long-term strength."
        )
    pct = ((sma_200 - price) / sma_200) * 100
    return (
        f"📉 The price (${price:,.2f}) is **below** the 200-day average "
        f"(${sma_200:,.2f}) by {pct:.1f}%. "
        "That's like slipping under the class average — "
        "the stock may be in a weaker trend right now."
    )


def chart_school_candlestick() -> str:
    """
    Return the 'Chart School' lesson that explains a candlestick like
    a battle between the Green Team and the Red Team.
    """
    return """
### 🏫 Chart School: Reading a Candlestick

Imagine every trading day is a **tug-of-war** between two teams:

| Team | Color | Goal |
|------|-------|------|
| **Green Team** (Buyers) | 🟩 | Pull the price **UP** |
| **Red Team** (Sellers) | 🟥 | Pull the price **DOWN** |

**Parts of a candlestick:**

```
    │  ← Upper Wick (the losing team's best try)
   ┌┴┐
   │ │ ← Body (who won the day)
   └┬┘
    │  ← Lower Wick (the other team's best try)
```

- **Green (hollow) candle** → The Green Team won! The price *closed*
  higher than it *opened*. The bottom of the body is the Open and the
  top is the Close.

- **Red (filled) candle** → The Red Team won. The price *closed* lower
  than it *opened*. The top of the body is the Open and the bottom is
  the Close.

- **Wicks (shadows)** → These show the highest and lowest prices reached
  during the day — like how far each team pulled the rope before the
  other team pulled back.

**Quick tips:**
- A **long green body** = Green Team dominated — strong buying day 💪
- A **long red body** = Red Team dominated — strong selling day
- **Tiny body + long wicks** = Neither team could win — the market is
  undecided (called a "Doji")

Now look at the chart above and see who's winning each day!
"""
