# ============================================================
# PHASE 3 — STRATEGY DEVELOPER
# File: 06_strategy.py
# Job: Turn signal into complete strategy with rules
# ============================================================

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TICKER      = "AAPL"
CAPITAL     = 10000    # starting capital $10,000
POSITION_PCT = 0.10   # 10% of capital per trade
STOP_LOSS   = 0.03    # 3% stop loss
TAKE_PROFIT = 0.06    # 6% take profit

# Load data
df = pd.read_csv(f"data/{TICKER}.csv", header=[0,1],
                 index_col=0, parse_dates=True)
df.columns = [col[0] for col in df.columns]
df['Return'] = df['Close'].pct_change()

# ============================================================
# STEP 1 — Rebuild Signal from Phase 2
# ============================================================

# Moving averages
df['SMA20'] = df['Close'].rolling(window=20).mean()
df['SMA50'] = df['Close'].rolling(window=50).mean()

# Volume filter
df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']

# RSI
def calculate_rsi(prices, period=14):
    delta    = prices.diff()
    gains    = delta.copy()
    losses   = delta.copy()
    gains[gains < 0]   = 0
    losses[losses > 0] = 0
    losses   = abs(losses)
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    rs       = avg_gain / avg_loss
    rsi      = 100 - (100 / (1 + rs))
    return rsi

df['RSI'] = calculate_rsi(df['Close'], period=14)

# Three condition signal
condition_trend  = df['SMA20'] > df['SMA50']
condition_volume = df['Volume_Ratio'] > 1.0
condition_rsi    = (df['RSI'] >= 50) & (df['RSI'] <= 70)

df['Signal'] = 0
df.loc[condition_trend & condition_volume & condition_rsi, 'Signal'] = 1
df.loc[(df['SMA20'] < df['SMA50']) & condition_volume, 'Signal'] = -1

print("Signal rebuilt successfully")
print(f"BUY signals:  {(df['Signal']==1).sum()} days")
print(f"SELL signals: {(df['Signal']==-1).sum()} days")