"""
FMP Client — Fetches daily OHLC price history from Financial Modeling Prep.

The API key is loaded internally from .env / st.secrets so it never
needs to be passed around or displayed in the UI.
"""

import os
import pathlib
import requests
import pandas as pd
from dotenv import load_dotenv

# Force-reload .env every time (picks up edits without restarting)
_env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

BASE_URL = "https://financialmodelingprep.com/stable"


def _clean_key(raw: str) -> str:
    """Strip whitespace, newlines, quotes, and BOM from a key string."""
    return raw.strip().strip('"').strip("'").strip("\n\r\t").lstrip("\ufeff")


def _get_api_key() -> str:
    """
    Resolve the FMP API key from environment or Streamlit secrets.
    Returns the key string, or raises ValueError if missing.
    """
    # 1. Try .env / OS environment
    key = _clean_key(os.getenv("FMP_API_KEY", ""))
    if key and key != "your_api_key_here":
        return key

    # 2. Try Streamlit secrets (deployed apps)
    try:
        import streamlit as st
        key = _clean_key(st.secrets.get("FMP_API_KEY", ""))
        if key:
            return key
    except Exception:
        pass

    raise ValueError("FMP_API_KEY not found in .env or Streamlit secrets.")


def fetch_daily_ohlc(ticker: str, years: int = 5) -> pd.DataFrame:
    """
    Pull *years* of daily OHLC data for *ticker*.

    Parameters
    ----------
    ticker : str
        Stock symbol, e.g. "AAPL".
    years : int, optional
        How many years of history to request (default 5).

    Returns
    -------
    pd.DataFrame
        Columns: date, open, high, low, close, volume
        Sorted ascending by date. Index is a default integer index.

    Raises
    ------
    ValueError
        If the API key is missing, or the API returns an error / empty data.
    requests.HTTPError
        If the HTTP request itself fails.
    """
    api_key = _get_api_key()
    ticker = ticker.strip().upper()

    url = f"{BASE_URL}/historical-price-eod/full"
    params = {"symbol": ticker, "apikey": api_key}

    response = requests.get(url, params=params, timeout=30)

    if not response.ok:
        body = response.text[:500]
        raise ValueError(
            f"FMP returned HTTP {response.status_code} for '{ticker}'. "
            f"Server response: {body}"
        )

    data = response.json()

    if isinstance(data, dict) and "Error Message" in data:
        raise ValueError(data["Error Message"])

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(
            f"No data returned for '{ticker}'. Check the symbol and try again."
        )

    df = pd.DataFrame(data)

    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])

    # API returns newest-first — flip to ascending
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def is_api_configured() -> bool:
    """Return True if a valid API key is available."""
    try:
        _get_api_key()
        return True
    except ValueError:
        return False


def test_connection() -> tuple[bool, str]:
    """
    Fetch AAPL daily history to verify the key works.
    Uses the modern /stable/ endpoint.
    Returns (success: bool, message: str).
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        return False, str(e)

    url = f"{BASE_URL}/historical-price-eod/full"
    params = {"symbol": "AAPL", "apikey": api_key}

    try:
        resp = requests.get(url, params=params, timeout=15)
        if not resp.ok:
            return False, f"FMP returned HTTP {resp.status_code}."
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return True, "Connection successful — API key is valid."
        return False, "Unexpected response from FMP. Check your API key."
    except requests.RequestException as e:
        return False, f"Network error: {e}"
