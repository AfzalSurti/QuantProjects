import pandas as pd
import numpy as np
import matplotlib .pyplot as plt

TICKER="AAPL"

df=pd.read_csv(f"data/{TICKER}.csv",header=[0,1],index_col=0,parse_dates=True)
df.columns=[col[0] for col in df.columns]

df['Return']=df['Close'].pct_change()

print(f"Loaded {len(df)} rows")
print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")

# step 2 - build the signal 

df['SMA-20']=df['Close'].rolling(window=20).mean() # calculates the 20-day simple moving average (SMA) of the closing price. The rolling() method creates a rolling window of size 20, and the mean() method calculates the average closing price within that window. The resulting SMA values are stored in a new column called 'SMA-20'.
df['SMA-50']=df['Close'].rolling(window=50).mean() # calculates the 50-day simple moving average (SMA) of the closing price. Similar to the previous line, it creates a rolling window of size 50 and calculates the average closing price within that window. The resulting SMA values are stored in a new column called 'SMA-50'.

print("first 55 rows")
print(df[['Close','SMA-20','SMA-50']].head(55))

# step-3 - genarate buy or sell signal

df['Signal']=0 # initializes a new column called 'Signal' with a default value of 0. This column will be used to store the trading signals (buy or sell) based on the relationship between the closing price and the moving averages.
df.loc[df['SMA-20']>df['SMA-50'], 'Signal']=1 # sets the 'Signal' column to 1 for rows where the 20-day SMA is greater than the 50-day SMA.
# what is a df.loc[] method? - The df.loc[] method is used to access a group of rows and columns by labels or a boolean array. In this case, it is used to set the 'Signal' column to 1 for rows where the condition (df['SMA-20'] > df['SMA-50']) is true.
df.loc[df['SMA-20']<df['SMA-50'],'Signal']=-1 # sets the 'Signal' column to -1 for rows where the 20-day SMA is less than the 50-day SMA.

print("Signal value counts:")
print(df['Signal'].value_counts())

# step-4 - test if signal has edge

df['Signal_Today']=df['Signal'].shift(1) # creates a new column called 'Signal_Today' by shifting the 'Signal' column down by one row. This means that the signal for the current day will be based on the signal from the previous day.

buy_days=df[df['Signal_Today']==1]['Return']
sell_days=df[df['Signal_Today']==-1]['Return']
all_days=df['Return'].dropna() # creates a new Series called 'all_days' by dropping any rows with missing values in the 'Return' column. This will be used to calculate the overall return for all days, regardless of the signal.

print("\n=== EDGE ANALYSIS ===")
print(f"Total days analyzed: {len(all_days)}")
print(f"\nBUY signal days ({len(buy_days)} days):")
print(f"  Mean daily return: {buy_days.mean():.4f} ({buy_days.mean()*100:.3f}%)")
print(f"  Win rate:          {(buy_days > 0).mean():.3f} ({(buy_days > 0).mean()*100:.1f}%)")
print(f"  Std (volatility):  {buy_days.std():.4f}")

print(f"\nSELL signal days ({len(sell_days)} days):")
print(f"  Mean daily return: {sell_days.mean():.4f} ({sell_days.mean()*100:.3f}%)")
print(f"  Win rate:          {(sell_days > 0).mean():.3f} ({(sell_days > 0).mean()*100:.1f}%)")
print(f"  Std (volatility):  {sell_days.std():.4f}")

print(f"\nAll days (no signal):")
print(f"  Mean daily return: {all_days.mean():.4f} ({all_days.mean()*100:.3f}%)")
print(f"  Win rate:          {(all_days > 0).mean():.3f} ({(all_days > 0).mean()*100:.1f}%)")


# ============================================================
# STEP 5 — VISUALIZE
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
fig.suptitle(f'{TICKER} — Moving Average Signal 2018-2024', fontsize=14)

# --- Chart 1: Price with SMAs ---
axes[0].plot(df.index, df['Close'], color='blue',
             linewidth=1, alpha=0.7, label='Close Price')
axes[0].plot(df.index, df['SMA-20'], color='orange',
             linewidth=1.5, label='SM-20 (fast)')
axes[0].plot(df.index, df['SMA-50'], color='red',
             linewidth=1.5, label='SM-50 (slow)')

# Shade background green when signal=BUY
axes[0].fill_between(df.index, df['Close'].min(), df['Close'].max(),
                     where=(df['Signal'] == 1),
                     alpha=0.1, color='green', label='BUY zone')
axes[0].fill_between(df.index, df['Close'].min(), df['Close'].max(),
                     where=(df['Signal'] == -1),
                     alpha=0.1, color='red', label='SELL zone')

axes[0].set_title('Price + SM-20 + SM-50 (Green=BUY zone, Red=SELL zone)')
axes[0].set_ylabel('Price ($)')
axes[0].legend(loc='upper left')
axes[0].grid(True, alpha=0.3)

# --- Chart 2: Signal over time ---
axes[1].plot(df.index, df['Signal'], color='purple',
             linewidth=1, drawstyle='steps-post')
axes[1].axhline(y=0, color='black', linewidth=0.8)
axes[1].fill_between(df.index, 0, df['Signal'],
                     where=(df['Signal'] == 1),
                     alpha=0.4, color='green')
axes[1].fill_between(df.index, 0, df['Signal'],
                     where=(df['Signal'] == -1),
                     alpha=0.4, color='red')
axes[1].set_title('Signal Over Time (+1=BUY, -1=SELL)')
axes[1].set_ylabel('Signal')
axes[1].set_yticks([-1, 0, 1])
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/signals.png', dpi=150)
plt.show()

print("Chart saved to data/signals.png")