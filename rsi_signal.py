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


# STEP 4 — TEST EDGE — THE MOMENT OF TRUTH


df['Signal_Today'] = df['Signal'].shift(1)

buy_days  = df[df['Signal_Today'] == 1]['Return']
sell_days = df[df['Signal_Today'] == -1]['Return']
all_days  = df['Return'].dropna()

print("\n=== EDGE PROGRESSION ===")
print(f"{'Signal':<30} {'Mean Return':>12} {'Win Rate':>10} {'Days':>6}")
print("-" * 62)
print(f"{'All days (benchmark)':<30} {all_days.mean()*100:>11.3f}% {(all_days>0).mean()*100:>9.1f}% {len(all_days):>6}")
print(f"{'Old: SMA only':<30} {'0.121%':>12} {'52.8%':>10} {'954':>6}")
print(f"{'Improved: SMA+Volume':<30} {'0.183%':>12} {'53.7%':>10} {'389':>6}")
print(f"{'New: SMA+Volume+RSI':<30} {buy_days.mean()*100:>11.3f}% {(buy_days>0).mean()*100:>9.1f}% {len(buy_days):>6}")

# Statistical significance
t_stat, p_value = stats.ttest_ind(buy_days.dropna(), all_days.dropna())

print(f"\n=== STATISTICAL TEST ===")
print(f"P-value: {p_value:.4f}")
print()
if p_value < 0.05:
    print("✅ STATISTICALLY SIGNIFICANT — edge is real")
    print("   This signal is worth backtesting")
elif p_value < 0.10:
    print("⚠️  BORDERLINE — weak evidence of edge")
    print("   Proceed to backtest with caution")
else:
    print("❌ NOT SIGNIFICANT — could be random noise")
    print("   Consider adding more conditions")


# ============================================================
# STEP 5 — VISUALIZE
# ============================================================

fig, axes = plt.subplots(4, 1, figsize=(14, 14))
fig.suptitle(f'{TICKER} — Three Condition Signal', fontsize=14)

# Chart 1: Price with SMAs
axes[0].plot(df.index, df['Close'],
             color='blue', linewidth=1, alpha=0.6, label='Price')
axes[0].plot(df.index, df['SMA20'],
             color='orange', linewidth=1.5, label='SMA20')
axes[0].plot(df.index, df['SMA50'],
             color='red', linewidth=1.5, label='SMA50')
axes[0].fill_between(df.index, df['Close'].min(), df['Close'].max(),
                     where=(df['Signal'] == 1),
                     alpha=0.2, color='green', label='BUY signal')
axes[0].set_title('Price + Moving Averages')
axes[0].set_ylabel('Price ($)')
axes[0].legend(loc='upper left', fontsize=8)
axes[0].grid(True, alpha=0.3)

# Chart 2: RSI
axes[1].plot(df.index, df['RSI'], color='purple', linewidth=1)
axes[1].axhline(y=70, color='red', linewidth=1.5,
                linestyle='--', label='Overbought (70)')
axes[1].axhline(y=50, color='green', linewidth=1.5,
                linestyle='--', label='Midline (50)')
axes[1].axhline(y=30, color='blue', linewidth=1.5,
                linestyle='--', label='Oversold (30)')
axes[1].fill_between(df.index, 50, 70,
                     alpha=0.1, color='green', label='Sweet spot')
axes[1].set_title('RSI (Sweet spot = 50 to 70)')
axes[1].set_ylabel('RSI')
axes[1].set_ylim(0, 100)
axes[1].legend(loc='upper right', fontsize=8)
axes[1].grid(True, alpha=0.3)

# Chart 3: Volume ratio
axes[2].plot(df.index, df['Volume_Ratio'],
             color='gray', linewidth=0.8)
axes[2].axhline(y=1.0, color='black', linewidth=1.5, linestyle='--')
axes[2].fill_between(df.index, 1.0, df['Volume_Ratio'],
                     where=(df['Volume_Ratio'] > 1.0),
                     alpha=0.3, color='green')
axes[2].set_title('Volume Ratio (above 1.0 = high volume)')
axes[2].set_ylabel('Ratio')
axes[2].grid(True, alpha=0.3)

# Chart 4: Final signal
axes[3].plot(df.index, df['Signal'],
             color='purple', linewidth=1, drawstyle='steps-post')
axes[3].fill_between(df.index, 0, df['Signal'],
                     where=(df['Signal'] == 1),
                     alpha=0.4, color='green', label='BUY')
axes[3].fill_between(df.index, 0, df['Signal'],
                     where=(df['Signal'] == -1),
                     alpha=0.4, color='red', label='SELL')
axes[3].set_title('Final Signal (+1=BUY, -1=SELL, 0=HOLD)')
axes[3].set_ylabel('Signal')
axes[3].set_yticks([-1, 0, 1])
axes[3].legend(loc='upper right', fontsize=8)
axes[3].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/rsi_signal.png', dpi=150)
plt.close()

print("\nChart saved to data/rsi_signal.png")
print("\n=== DONE ===")