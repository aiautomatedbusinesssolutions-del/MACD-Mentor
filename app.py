"""
MACD Mentor — Spot the Trend, Skip the Stress.
Phase 2: Candlestick Chart + 200-day SMA + MACD Indicator
"""

import pathlib
from dotenv import load_dotenv

# Load .env BEFORE any other app imports so the key is available everywhere
load_dotenv(pathlib.Path(__file__).resolve().parent / ".env", override=True)

import os

import pandas as pd
import streamlit as st
import streamlit_analytics2 as streamlit_analytics
from streamlit_lightweight_charts import renderLightweightCharts

from logic.fmp_client import fetch_daily_ohlc, is_api_configured, test_connection
from logic.indicators import compute_sma, compute_macd
from logic.translator import explain_signal
from analysis.backtester import pattern_match_30d

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MACD Mentor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide the sidebar toggle completely
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Analytics Tracking ────────────────────────────────────────────────────────
with streamlit_analytics.track(unsafe_password=os.getenv("ANALYTICS_PASSWORD", "")):

    # ── Title ────────────────────────────────────────────────────────────────
    st.title("📈 MACD Mentor")
    st.caption("Spot the Trend, Skip the Stress.")

    # ── API Key Check + Connection Test ──────────────────────────────────────
    if not is_api_configured():
        st.warning("System setup incomplete. Please check your configuration.")
        st.stop()

    # One-time connection test (cached so it only runs once per session)
    if "connection_tested" not in st.session_state:
        ok, msg = test_connection()
        st.session_state["connection_tested"] = True
        st.session_state["connection_ok"] = ok
        st.session_state["connection_msg"] = msg

    if not st.session_state["connection_ok"]:
        st.error(st.session_state["connection_msg"])
        st.stop()

    # ── Ticker Input + Analyze Button ────────────────────────────────────────
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        ticker_input = st.text_input(
            "Enter a ticker symbol",
            placeholder="e.g. AAPL, MSFT, TSLA…",
            label_visibility="collapsed",
            value=st.session_state.get("ticker_text", ""),
        )
        # Force-uppercase: if the user typed lowercase, rewrite and rerun
        if ticker_input and ticker_input != ticker_input.strip().upper():
            st.session_state["ticker_text"] = ticker_input.strip().upper()
            st.rerun()

    with col_btn:
        run = st.button("🚀 Analyze", use_container_width=True)

    ticker = ticker_input.strip().upper() if ticker_input else ""

    if not run:
        st.stop()

    if not ticker:
        st.warning("Enter a ticker symbol to analyze (e.g. AAPL).")
        st.stop()

    # ── Fetch Data ───────────────────────────────────────────────────────────
    with st.spinner(f"Fetching 5 years of daily data for **{ticker}**…"):
        try:
            df = fetch_daily_ohlc(ticker, years=5)
        except Exception:
            st.error("Ticker not found. Please check the symbol and try again.")
            st.stop()

    # ── Compute Indicators ───────────────────────────────────────────────────
    df = compute_sma(df, window=200)
    df = compute_macd(df)

    # ── Signal Detection + Historical Pattern Match ─────────────────────────
    mentor = explain_signal(df)
    history = pattern_match_30d(df, mentor["signal"])

    # ── Prepare chart data ───────────────────────────────────────────────────
    st.subheader(f"📊 {ticker} — Daily Chart")

    # Candlestick data: list of dicts with time, open, high, low, close
    candle_data = df[["date", "open", "high", "low", "close"]].copy()
    candle_data["time"] = candle_data["date"].dt.strftime("%Y-%m-%d")
    candles = candle_data[["time", "open", "high", "low", "close"]].to_dict("records")

    # 200-day SMA: list of dicts with time, value (skip NaN rows)
    sma_df = df[["date", "sma_200"]].dropna(subset=["sma_200"]).copy()
    sma_df["time"] = sma_df["date"].dt.strftime("%Y-%m-%d")
    sma_data = [{"time": r["time"], "value": r["sma_200"]} for _, r in sma_df.iterrows()]

    # MACD Histogram: list of dicts with time, value, color
    hist_data = []
    for _, r in df.iterrows():
        v = r["macd_histogram"]
        if pd.notna(v):
            hist_data.append({
                "time": r["date"].strftime("%Y-%m-%d"),
                "value": round(v, 4),
                "color": "#089981" if v >= 0 else "#f23645",
            })

    # MACD Line
    macd_line_data = []
    for _, r in df.iterrows():
        if pd.notna(r["macd_line"]):
            macd_line_data.append({
                "time": r["date"].strftime("%Y-%m-%d"),
                "value": round(r["macd_line"], 4),
            })

    # Signal Line
    signal_line_data = []
    for _, r in df.iterrows():
        if pd.notna(r["signal_line"]):
            signal_line_data.append({
                "time": r["date"].strftime("%Y-%m-%d"),
                "value": round(r["signal_line"], 4),
            })

    # ── Shared layout tokens ─────────────────────────────────────────────────
    _TV_BG   = "#131722"
    _TV_GRID = "#2a2e39"
    _TV_TEXT = "#d1d4dc"

    _time_scale = {
        "borderColor": _TV_GRID,
        "fixLeftEdge": True,
        "fixRightEdge": True,
    }

    # ── Pane 1 — Price + SMA ─────────────────────────────────────────────────
    price_chart = {
        "chart": {
            "height": 500,
            "layout": {
                "background": {"type": "solid", "color": _TV_BG},
                "textColor": _TV_TEXT,
                "fontFamily": "Trebuchet MS, Arial, sans-serif",
            },
            "grid": {
                "vertLines": {"color": _TV_GRID},
                "horzLines": {"color": _TV_GRID},
            },
            "crosshair": {"mode": 0},
            "rightPriceScale": {
                "borderColor": _TV_GRID,
                "scaleMargins": {"top": 0.1, "bottom": 0.08},
            },
            "timeScale": _time_scale,
        },
        "series": [
            {
                "type": "Candlestick",
                "data": candles,
                "options": {
                    "upColor": "#089981",
                    "downColor": "#f23645",
                    "borderUpColor": "#089981",
                    "borderDownColor": "#f23645",
                    "wickUpColor": "#089981",
                    "wickDownColor": "#f23645",
                },
            },
            {
                "type": "Line",
                "data": sma_data,
                "options": {
                    "color": "#e2b714",
                    "lineWidth": 2,
                    "crosshairMarkerVisible": False,
                    "priceLineVisible": False,
                    "title": "SMA 200",
                },
            },
        ],
    }

    # ── Pane 2 — MACD ────────────────────────────────────────────────────────
    macd_chart = {
        "chart": {
            "height": 200,
            "layout": {
                "background": {"type": "solid", "color": _TV_BG},
                "textColor": _TV_TEXT,
                "fontFamily": "Trebuchet MS, Arial, sans-serif",
            },
            "grid": {
                "vertLines": {"color": _TV_GRID},
                "horzLines": {"color": _TV_GRID},
            },
            "crosshair": {"mode": 0},
            "rightPriceScale": {
                "borderColor": _TV_GRID,
                "scaleMargins": {"top": 0.1, "bottom": 0.08},
            },
            "timeScale": {**_time_scale, "visible": False},
        },
        "series": [
            {
                "type": "Histogram",
                "data": hist_data,
                "options": {
                    "priceLineVisible": False,
                    "title": "Histogram",
                },
            },
            {
                "type": "Line",
                "data": macd_line_data,
                "options": {
                    "color": "#2962ff",
                    "lineWidth": 2,
                    "crosshairMarkerVisible": False,
                    "priceLineVisible": False,
                    "title": "MACD",
                },
            },
            {
                "type": "Line",
                "data": signal_line_data,
                "options": {
                    "color": "#ff6d00",
                    "lineWidth": 2,
                    "crosshairMarkerVisible": False,
                    "priceLineVisible": False,
                    "title": "Signal",
                },
            },
        ],
    }

    renderLightweightCharts([price_chart, macd_chart], key="macd_mentor")

    # ── Coach's Corner: Understanding MACD ───────────────────────────────────
    with st.container(border=True):
        st.markdown("### 📘 Coach's Corner: Understanding MACD")
        st.markdown(
            "- **MACD Line** (blue) — Measures **short-term energy**. "
            "It's the difference between a fast moving average (12-day) and a slow one (26-day). "
            "When the fast average pulls ahead, momentum is building.\n"
            "- **Signal Line** (orange) — A **smoothed guide** (9-day average of the MACD). "
            "Think of it as the calm voice that confirms whether the energy burst is real or just noise.\n"
            "- **Histogram** (green/red bars) — The **gap** between the MACD and Signal lines. "
            "Tall green bars = momentum is strong and rising. "
            "Tall red bars = momentum is fading fast.\n\n"
            "**Key takeaway:** When the MACD Line crosses *above* the Signal Line, "
            "momentum is shifting bullish. When it crosses *below*, momentum is turning bearish."
        )

    # ── Mentor's Market Compass ──────────────────────────────────────────────
    st.subheader(f"🧭 Mentor's Market Compass — {ticker}")

    color_map = {"green": "#26a69a", "red": "#ef5350", "gray": "#9e9e9e"}
    accent = color_map[mentor["color"]]

    col_light, col_text = st.columns([1, 5])

    with col_light:
        st.markdown(
            f'<div style="font-size:4.5rem; line-height:1; text-align:center; padding-top:0.15rem;">'
            f'{mentor["icon"]}</div>',
            unsafe_allow_html=True,
        )

    with col_text:
        # Build the history line — always shown when data is available
        history_html = ""
        if history and history["small_sample"]:
            history_html = (
                '<p style="font-size:0.95rem; color:#aaa; margin:0.5rem 0 0 0; '
                'border-top:1px solid rgba(255,255,255,0.1); padding-top:0.5rem;">'
                '📊 <strong>Historical Probability:</strong> '
                'Sample size too small for historical probability (less than 3 occurrences).'
                '</p>'
            )
        elif history:
            sign = "+" if history["avg_return"] >= 0 else ""
            history_html = (
                f'<p style="font-size:0.95rem; color:#aaa; margin:0.5rem 0 0 0; '
                f'border-top:1px solid rgba(255,255,255,0.1); padding-top:0.5rem;">'
                f'📊 <strong>Historical Probability:</strong> '
                f'In the last 5 years, this setup appeared <strong>{history["matches"]}</strong> times. '
                f'<strong>{history["win_pct"]}%</strong> of the time, the price was higher 30 days later, '
                f'with an average move of <strong>{sign}{history["avg_return"]}%</strong>.'
                f'</p>'
            )

        st.markdown(
            f"""
            <div style="
                border-left: 4px solid {accent};
                padding: 0.6rem 1rem;
            ">
                <p style="font-size:1.5rem; font-weight:800; color:{accent}; margin:0 0 0.3rem 0; letter-spacing:0.03em;">
                    {mentor["headline"]}
                </p>
                <p style="font-size:0.95rem; color:#ccc; margin:0;">
                    {mentor["why"]}
                </p>
                {history_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Recent Historical Matches Table ──────────────────────────────────────
    if history and not history["small_sample"] and history["recent"]:
        st.subheader("Recent Historical Matches (30-Day Outlook)")

        table_data = []
        for m in reversed(history["recent"]):  # newest first
            pct = m["pct_change"]
            sign = "+" if pct >= 0 else ""
            table_data.append({
                "Date": m["date"].strftime("%Y-%m-%d"),
                "Entry Price": f"${m['entry_price']:,.2f}",
                "Price 30 Days Later": f"${m['price_30d']:,.2f}",
                "30-Day Move": f"{sign}{pct:.2f}%",
            })

        table_df = pd.DataFrame(table_data)

        # Color-code the 30-Day Move column
        def _color_move(val: str) -> str:
            if val.startswith("+"):
                return "color: #26a69a"
            if val.startswith("-"):
                return "color: #ef5350"
            return ""

        styled = table_df.style.applymap(_color_move, subset=["30-Day Move"])
        styled = styled.set_properties(**{"text-align": "right"}, subset=["Entry Price", "Price 30 Days Later", "30-Day Move"])
        styled = styled.set_properties(**{"text-align": "left"}, subset=["Date"])
        styled = styled.hide(axis="index")

        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Mentor's Masterclass: The Strategy ───────────────────────────────────
    with st.container(border=True):
        st.markdown("### 🎓 Mentor's Masterclass: The Strategy")
        st.markdown(
            "The **200-day SMA** tells us the **Season** — is the market in "
            "**Summer** (price above the average, long-term uptrend) or "
            "**Winter** (price below, long-term downtrend)?\n\n"
            "The **MACD** tells us the **Weather** — is it "
            "**Sunny** (MACD above Signal, momentum rising) or "
            "**Rainy** (MACD below Signal, momentum fading) for the next 30 days?\n\n"
            "**When Season and Weather agree**, the signal is strongest:\n"
            "- 🟢 **Summer + Sunny** = Green Wave (GO)\n"
            "- 🔴 **Winter + Rainy** = Red Flag (STOP)\n"
            "- 🟡 **Mixed** = Yellow Light (CAUTION) — one says go, the other says wait\n\n"
            "**About the Historical Matches:** History doesn't repeat, but it often rhymes. "
            "We scan the last 5 years to find every day that had the *exact same* Season + Weather combo as today, "
            "then measure what happened 30 days later. "
            "The 10 most recent examples are shown in the table so you can see how similar \"weather\" behaved in the past."
        )

    # ── Disclaimer ───────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "⚠️ **Disclaimer:** This app is for educational purposes only. "
        "MACD signals are not financial advice. Past performance does not "
        "guarantee future results. Always do your own research."
    )
