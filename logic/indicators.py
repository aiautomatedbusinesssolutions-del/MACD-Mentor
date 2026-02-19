"""
Technical Indicators — MACD (12, 26, 9) and 200-day SMA.
"""

import pandas as pd


def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Add MACD columns to *df* (must contain a 'close' column).

    New columns added:
        ema_fast, ema_slow, macd_line, signal_line, macd_histogram
    """
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = df["ema_fast"] - df["ema_slow"]
    df["signal_line"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["signal_line"]
    return df


def compute_sma(df: pd.DataFrame, window: int = 200) -> pd.DataFrame:
    """
    Add a Simple Moving Average column (`sma_{window}`) to *df*.
    """
    df = df.copy()
    df[f"sma_{window}"] = df["close"].rolling(window=window).mean()
    return df
