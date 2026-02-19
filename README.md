# MACD Mentor

**Spot the Trend, Skip the Stress.**

MACD Mentor is an educational stock analysis app that combines candlestick charting, the MACD momentum indicator, and the 200-day Simple Moving Average into a single, beginner-friendly dashboard. It translates technical signals into plain-English guidance using a visual "stoplight" system.

## Features

- **TradingView-style Candlestick Chart** — Interactive daily price chart powered by TradingView's Lightweight Charts library with dark theme, crosshair, and pan/zoom
- **200-day SMA Overlay** — Long-term trend line displayed in gold to show whether the market is in "Summer" (uptrend) or "Winter" (downtrend)
- **MACD Indicator Panel** — Synchronized subplot showing the MACD Line, Signal Line, and Histogram with color-coded momentum bars
- **Mentor's Market Compass** — A stoplight signal (Green / Yellow / Red) based on the agreement between trend (SMA) and momentum (MACD)
- **30-Day Historical Probability** — Scans 5 years of data to find every day with the same signal setup, then reports what percentage of the time the price was higher 30 days later
- **Recent Historical Matches Table** — The 10 most recent pattern matches with entry price, 30-day outcome, and color-coded returns
- **Educational Boxes** — Coach's Corner explains MACD in beginner terms; Mentor's Masterclass explains the full strategy using a Season + Weather metaphor

## Tech Stack

- **Python 3.10+**
- **Streamlit** — Web framework
- **streamlit-lightweight-charts** — TradingView Lightweight Charts wrapper
- **pandas** — Data processing and indicator calculations
- **requests** — API calls to Financial Modeling Prep
- **python-dotenv** — Environment variable management

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MACD-Mentor.git
   cd MACD-Mentor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your FMP API key:
   ```
   FMP_API_KEY=your_api_key_here
   ```
   Get a free key at [financialmodelingprep.com](https://financialmodelingprep.com/developer).

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
MACD-Mentor/
  app.py                  # Main Streamlit application
  requirements.txt        # Python dependencies
  .env                    # API key (not committed)
  logic/
    fmp_client.py         # FMP API data fetching
    indicators.py         # MACD and SMA calculations
    translator.py         # Signal detection and plain-English explanations
  analysis/
    backtester.py         # Historical pattern matching (30-day forward returns)
```

## Disclaimer

This app is for educational purposes only. MACD signals are not financial advice. Past performance does not guarantee future results. Always do your own research.
