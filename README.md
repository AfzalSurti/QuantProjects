# Fetching Real Market Data

A step-by-step educational project that builds a complete quantitative trading workflow in Python — from downloading real market data to signal research, strategy simulation, backtesting, and risk analysis.

Default ticker: **AAPL** (Apple)  
Date range: **2018-01-01 → 2024-01-01**  
Starting capital: **$10,000**

---

## What This Project Does

You walk through the same stages a quant research pipeline typically uses:

1. Fetch historical prices from Yahoo Finance  
2. Explore and clean the data  
3. Build and improve trading signals  
4. Turn signals into a full strategy with position sizing and risk rules  
5. Backtest with real performance metrics  
6. Stress-test the strategy through market crises  

---

## Project Pipeline

| # | File | Phase | What it does |
|---|------|--------|--------------|
| 1 | `2_fetch_data.py` | Data Engineer | Downloads OHLCV data with `yfinance` and saves it to `data/AAPL.csv` |
| 2 | `1_explore_data.py` | Data Exploration | Cleans columns, checks quality, finds crash/best days, plots price/volume/returns |
| 3 | `3_signals.py` | Signal Research | Builds SMA20/SMA50 crossover signals and tests if they have an edge |
| 4 | `4_improve_signal.py` | Signal Research | Adds a volume filter and runs a statistical significance test |
| 5 | `5_rsi_signal.py` | Signal Research | Adds RSI and creates a 3-condition buy signal |
| 6 | `6_strategy.py` | Strategy Developer | Simulates trades with capital, stop loss, and take profit |
| 7 | `7_backtest.py` | Backtester | Improves sizing/risk rules and reports CAGR, Sharpe, max drawdown |
| 8 | `8_risk.py` | Risk Manager | Stress-tests crisis periods, rolling Sharpe, and full risk profile |

Run them in order. Most scripts after fetch assume `data/AAPL.csv` already exists.

---

## Final Strategy Rules

Used in `7_backtest.py` and `8_risk.py`:

**Buy when all three are true:**
- Trend: `SMA20 > SMA50`
- Volume: volume above its 20-day average
- Momentum: RSI between 50 and 70

**Sell when:**
- Stop loss hits (**-6%**), or
- Take profit hits (**+12%**), or
- Trend turns down with high volume (`SMA20 < SMA50` + volume confirmation)

**Position sizing:** 40% of capital per trade

Earlier scripts use simpler versions of this logic while the signal is being developed.

---

## Setup

### Requirements

- Python 3.9+
- Packages:

```bash
pip install yfinance pandas numpy matplotlib scipy
```

### Fetch data first

```bash
python 2_fetch_data.py
```

This creates `data/AAPL.csv`.

### Run the rest of the pipeline

```bash
python 1_explore_data.py
python 3_signals.py
python 4_improve_signal.py
python 5_rsi_signal.py
python 6_strategy.py
python 7_backtest.py
python 8_risk.py
```

Charts are saved under `data/`.

---

## Project Structure

```text
FetchingRealMarketData/
├── 2_fetch_data.py          # Download market data
├── 1_explore_data.py        # Explore & visualize raw data
├── 3_signals.py             # SMA crossover signal
├── 4_improve_signal.py      # SMA + volume filter
├── 5_rsi_signal.py          # SMA + volume + RSI
├── 6_strategy.py            # Trade simulation
├── 7_backtest.py            # Performance metrics
├── 8_risk.py                # Stress tests & risk profile
├── data/
│   ├── AAPL.csv
│   ├── exploration.png
│   ├── signals.png
│   ├── improved_signal.png
│   ├── rsi_signal.png
│   ├── strategy_performance.png
│   ├── backtest_fixed.png
│   └── risk_analysis.png
└── README.md
```

---

## Key Concepts

### What is a ticker?

A short code for a publicly traded company:

| Ticker | Company |
|--------|---------|
| `AAPL` | Apple |
| `MSFT` | Microsoft |
| `TSLA` | Tesla |
| `GOOGL` | Alphabet (Google) |
| `RELIANCE.NS` | Reliance Industries (NSE India) |
| `TCS.NS` | TCS (NSE India) |

Change `TICKER` at the top of each script to test another stock. Re-run `2_fetch_data.py` with the new ticker first.

### Libraries used

| Library | Role |
|---------|------|
| `yfinance` | Downloads free historical market data from Yahoo Finance |
| `pandas` | Tables, time series, indicators, filtering |
| `numpy` | Math and statistics |
| `matplotlib` | Charts and saved figures |
| `scipy` | Statistical tests (t-test / p-value for signal edge) |

---

## Risk Analysis Highlights (`8_risk.py`)

The risk module rebuilds the final strategy and then:

- Stress-tests three crisis windows:
  - **2018 Q4 selloff**
  - **COVID crash (2020)**
  - **2022 bear market**
- Computes rolling 6-month Sharpe ratio
- Prints a full risk profile:
  - CAGR
  - Max drawdown
  - Calmar ratio
  - Sharpe ratio
- Saves `data/risk_analysis.png`

---

## Notes

- This is a learning project, not financial advice.
- Backtests use historical data and ignore costs like commissions, slippage, and taxes unless you add them.
- Signals are shifted by one day in research/simulation so you do not trade on the same bar that generated the signal.
- Yahoo Finance data is free and good for learning; professional desks often use paid feeds (Bloomberg, Refinitiv, etc.).

---

## Quick Start Example

```bash
# 1. Install deps
pip install yfinance pandas numpy matplotlib scipy

# 2. Download AAPL data
python 2_fetch_data.py

# 3. Explore and research
python 1_explore_data.py
python 3_signals.py
python 4_improve_signal.py
python 5_rsi_signal.py

# 4. Simulate, backtest, and risk-check
python 6_strategy.py
python 7_backtest.py
python 8_risk.py
```
