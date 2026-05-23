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