# PHASE 2 — QUANT RESEARCHER
# Job: Add RSI to create three-condition signal

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

TICKER = "AAPL"

# Load data
df = pd.read_csv(f"data/{TICKER}.csv", header=[0,1],
                 index_col=0, parse_dates=True)
df.columns = [col[0] for col in df.columns]
df['Return'] = df['Close'].pct_change()

# STEP 1 — Calculate RSI from scratch
# We build it manually so you understand every step

def calculate_rsi(prices, period=14):
    
    # Step 1: Calculate daily price changes
    delta = prices.diff()
    # diff() = today's price - yesterday's price
    # Positive = up day, Negative = down day

    # Step 2: Separate gains and losses
    gains = delta.copy()
    losses = delta.copy()
    
    gains[gains < 0] = 0      # keep only positive days
    losses[losses > 0] = 0    # keep only negative days
    losses = abs(losses)      # make losses positive numbers

    # Step 3: Calculate rolling average gain and loss
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()

    # Step 4: Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

df['RSI'] = calculate_rsi(df['Close'], period=14)

print("=== RSI STATS ===")
print(df['RSI'].describe())
print(f"\nDays RSI > 70 (overbought): {(df['RSI'] > 70).sum()}")
print(f"Days RSI < 30 (oversold):   {(df['RSI'] < 30).sum()}")
print(f"Days RSI 50-70 (sweet spot): {((df['RSI'] >= 50) & (df['RSI'] <= 70)).sum()}")


# STEP 2 — Build All Indicators
# 

# Trend indicators
df['SMA20'] = df['Close'].rolling(window=20).mean()
df['SMA50'] = df['Close'].rolling(window=50).mean()

# Volume indicator
df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']

# 
# STEP 3 — Three Condition Signal


df['Signal'] = 0

# Define each condition separately — easier to read and debug
condition_trend  = df['SMA20'] > df['SMA50']
condition_volume = df['Volume_Ratio'] > 1.0
condition_rsi    = (df['RSI'] >= 50) & (df['RSI'] <= 70)

# All three must be true simultaneously
buy_condition = condition_trend & condition_volume & condition_rsi

df.loc[buy_condition, 'Signal'] = 1

# Sell condition — trend down + volume confirmed
sell_condition = (df['SMA20'] < df['SMA50']) & condition_volume
df.loc[sell_condition, 'Signal'] = -1

print("\n=== SIGNAL DISTRIBUTION ===")
print(df['Signal'].value_counts())

# How often each condition was true individually
print("\n=== CONDITION BREAKDOWN ===")
print(f"Trend up (SMA20>SMA50):     {condition_trend.sum()} days")
print(f"High volume:                {condition_volume.sum()} days")
print(f"RSI in sweet spot (50-70):  {condition_rsi.sum()} days")
print(f"ALL THREE true (BUY signal): {buy_condition.sum()} days")