# ============================================================
# PHASE 2 — QUANT RESEARCHER
# File: 04_improved_signal.py
# Job: Add volume filter to improve signal quality
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

TICKER = "AAPL"

# Load data
df = pd.read_csv(f"data/{TICKER}.csv", header=[0,1], index_col=0, parse_dates=True)
df.columns = [col[0] for col in df.columns]
df['Return'] = df['Close'].pct_change()

# ============================================================
# STEP 1 — Build All Indicators
# ============================================================

df['SMA20'] = df['Close'].rolling(window=20).mean()
df['SMA50'] = df['Close'].rolling(window=50).mean()
df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']

print("=== VOLUME RATIO STATS ===")
print(df['Volume_Ratio'].describe())

# ============================================================
# STEP 2 — Build Improved Signal
# ============================================================

df['Signal'] = 0

trend_up   = df['SMA20'] > df['SMA50']
trend_down = df['SMA20'] < df['SMA50']
high_volume = df['Volume_Ratio'] > 1.0

df.loc[trend_up   & high_volume, 'Signal'] = 1
df.loc[trend_down & high_volume, 'Signal'] = -1

print("\n=== SIGNAL DISTRIBUTION ===")
print(df['Signal'].value_counts())

# ============================================================
# STEP 3 — COMPARE OLD VS NEW SIGNAL
# ============================================================

df['Signal_Today'] = df['Signal'].shift(1)

buy_days  = df[df['Signal_Today'] == 1]['Return']
sell_days = df[df['Signal_Today'] == -1]['Return']
all_days  = df['Return'].dropna()

print("\n=== OLD SIGNAL (no volume filter) ===")
print(f"BUY  mean return: 0.121%  win rate: 52.8%")
print(f"SELL mean return: 0.129%  win rate: 54.7%")
print(f"ALL  mean return: 0.123%  win rate: 53.3%")

print("\n=== NEW SIGNAL (with volume filter) ===")
print(f"Total days analyzed: {len(all_days)}")
print(f"\nBUY signal days ({len(buy_days)} days):")
print(f"  Mean daily return: {buy_days.mean()*100:.3f}%")
print(f"  Win rate:          {(buy_days > 0).mean()*100:.1f}%")
print(f"  Std (volatility):  {buy_days.std()*100:.3f}%")
print(f"\nSELL signal days ({len(sell_days)} days):")
print(f"  Mean daily return: {sell_days.mean()*100:.3f}%")
print(f"  Win rate:          {(sell_days > 0).mean()*100:.1f}%")
print(f"  Std (volatility):  {sell_days.std()*100:.3f}%")
print(f"\nAll days (benchmark):")
print(f"  Mean daily return: {all_days.mean()*100:.3f}%")
print(f"  Win rate:          {(all_days > 0).mean()*100:.1f}%")

print("\n=== EDGE COMPARISON ===")
print(f"BUY days vs ALL days:")
print(f"  Difference: {(buy_days.mean() - all_days.mean())*100:.3f}%")
if buy_days.mean() > all_days.mean():
    print(f"  Result: BUY signal OUTPERFORMS market ✅")
else:
    print(f"  Result: BUY signal UNDERPERFORMS market ❌")

# ============================================================
# STEP 4 — STATISTICAL SIGNIFICANCE TEST
# ============================================================

t_stat, p_value = stats.ttest_ind(buy_days.dropna(), all_days.dropna())

print("\n=== STATISTICAL SIGNIFICANCE ===")
print(f"T-statistic: {t_stat:.4f}")
print(f"P-value:     {p_value:.4f}")
print()
if p_value < 0.05:
    print("P-value < 0.05 → Result is STATISTICALLY SIGNIFICANT ✅")
    print("The edge is REAL — not just random noise")
else:
    print("P-value > 0.05 → Result is NOT statistically significant ❌")
    print("The edge could be random noise — be careful")

# ============================================================
# STEP 5 — VISUALIZE IMPROVED SIGNAL
# ALL prints are done — chart comes last
# Closing chart window will NOT block output anymore
# ============================================================

fig, axes = plt.subplots(3, 1, figsize=(14, 11))
fig.suptitle(f'{TICKER} — Improved Signal with Volume Filter', fontsize=14)

axes[0].plot(df.index, df['Close'],
             color='blue', linewidth=1, alpha=0.7, label='Price')
axes[0].plot(df.index, df['SMA20'],
             color='orange', linewidth=1.5, label='SMA20')
axes[0].plot(df.index, df['SMA50'],
             color='red', linewidth=1.5, label='SMA50')
axes[0].fill_between(df.index, df['Close'].min(), df['Close'].max(),
                     where=(df['Signal'] == 1),
                     alpha=0.15, color='green', label='BUY signal')
axes[0].fill_between(df.index, df['Close'].min(), df['Close'].max(),
                     where=(df['Signal'] == -1),
                     alpha=0.15, color='red', label='SELL signal')
axes[0].set_title('Price + Moving Averages + Signal Zones')
axes[0].set_ylabel('Price ($)')
axes[0].legend(loc='upper left', fontsize=8)
axes[0].grid(True, alpha=0.3)

axes[1].bar(df.index, df['Volume'],
            color='gray', alpha=0.5, width=1, label='Volume')
axes[1].plot(df.index, df['Volume_SMA20'],
             color='blue', linewidth=1.5, label='Volume SMA20')
axes[1].set_title('Volume (bars) vs 20-day Average (blue line)')
axes[1].set_ylabel('Volume')
axes[1].legend(loc='upper right', fontsize=8)
axes[1].grid(True, alpha=0.3)

axes[2].plot(df.index, df['Volume_Ratio'],
             color='purple', linewidth=0.8)
axes[2].axhline(y=1.0, color='black',
                linewidth=1.5, linestyle='--', label='Average (1.0)')
axes[2].axhline(y=2.0, color='red',
                linewidth=1, linestyle='--', label='2x average')
axes[2].fill_between(df.index, 1.0, df['Volume_Ratio'],
                     where=(df['Volume_Ratio'] > 1.0),
                     alpha=0.3, color='green', label='Above average')
axes[2].fill_between(df.index, df['Volume_Ratio'], 1.0,
                     where=(df['Volume_Ratio'] < 1.0),
                     alpha=0.3, color='red', label='Below average')
axes[2].set_title('Volume Ratio (above 1.0 = high volume day)')
axes[2].set_ylabel('Ratio')
axes[2].legend(loc='upper right', fontsize=8)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/improved_signal.png', dpi=150)
plt.close()

print("\nChart saved to data/improved_signal.png")
print("\nDone. All output printed before chart.")