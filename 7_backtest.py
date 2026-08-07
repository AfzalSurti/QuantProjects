# ============================================================
# PHASE 4 — BACKTESTER
# File: 07_backtest.py
# Job: Fix position sizing + stop loss, add real metrics
# ============================================================

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TICKER       = "AAPL"
CAPITAL      = 10000
POSITION_PCT = 0.40    # FIX 2: was 0.10, now 0.40
STOP_LOSS    = 0.06    # FIX 1: was 0.03, now 0.06
TAKE_PROFIT  = 0.12    # widened proportionally (2:1 ratio kept)

df = pd.read_csv(f"data/{TICKER}.csv", header=[0,1],
                 index_col=0, parse_dates=True)
df.columns = [col[0] for col in df.columns]
df['Return'] = df['Close'].pct_change()

df['SMA20'] = df['Close'].rolling(window=20).mean()
df['SMA50'] = df['Close'].rolling(window=50).mean()
df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']

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

condition_trend  = df['SMA20'] > df['SMA50']
condition_volume = df['Volume_Ratio'] > 1.0
condition_rsi    = (df['RSI'] >= 50) & (df['RSI'] <= 70)

df['Signal'] = 0
df.loc[condition_trend & condition_volume & condition_rsi, 'Signal'] = 1
df.loc[(df['SMA20'] < df['SMA50']) & condition_volume, 'Signal'] = -1
     
print(f"Signal rebuilt — BUY: {(df['Signal']==1).sum()} days, SELL: {(df['Signal']==-1).sum()} days")


# ============================================================
# STEP 2 — SIMULATOR WITH DAILY PORTFOLIO TRACKING
# ============================================================

capital     = CAPITAL
position    = 0
entry_price = 0
trade_log   = []
daily_value = []   # NEW — track value every single day

for i in range(1, len(df)):
    
    today  = df.index[i]
    price  = df['Close'].iloc[i]
    signal = df['Signal'].iloc[i-1]
    
    if position > 0:
        price_change = (price - entry_price) / entry_price
        
        if price_change <= -STOP_LOSS:
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital   += sell_value
            trade_log.append({'date': today, 'action': 'SELL',
                              'reason': 'STOP LOSS', 'price': price,
                              'shares': position, 'profit': profit,
                              'capital': capital})
            position = 0
            entry_price = 0
        
        elif price_change >= TAKE_PROFIT:
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital   += sell_value
            trade_log.append({'date': today, 'action': 'SELL',
                              'reason': 'TAKE PROFIT', 'price': price,
                              'shares': position, 'profit': profit,
                              'capital': capital})
            position = 0
            entry_price = 0
        
        elif signal == -1:
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital   += sell_value
            trade_log.append({'date': today, 'action': 'SELL',
                              'reason': 'SIGNAL EXIT', 'price': price,
                              'shares': position, 'profit': profit,
                              'capital': capital})
            position = 0
            entry_price = 0
    
    elif position == 0 and signal == 1:
        trade_capital = capital * POSITION_PCT
        shares = int(trade_capital / price)
        
        if shares > 0:
            cost = shares * price
            capital -= cost
            position = shares
            entry_price = price
            trade_log.append({'date': today, 'action': 'BUY',
                              'reason': 'SIGNAL ENTRY', 'price': price,
                              'shares': shares, 'profit': 0,
                              'capital': capital})
    
    # ── NEW — record portfolio value EVERY day ──────────────
    # Portfolio value = cash + (shares held × today's price)
    market_value = position * price
    total_value  = capital + market_value
    
    daily_value.append({'date': today, 'value': total_value})

print(f"\nSimulation complete — Total trades: {len(trade_log)}")


# ============================================================
# STEP 3 — PERFORMANCE METRICS
# ============================================================

value_df = pd.DataFrame(daily_value).set_index('date')
value_df['daily_return'] = value_df['value'].pct_change()

# --- CAGR ---
years = (df.index[-1] - df.index[0]).days / 365.25
final_value = value_df['value'].iloc[-1]
cagr = (final_value / CAPITAL) ** (1/years) - 1

# --- Sharpe Ratio ---
mean_daily_return = value_df['daily_return'].mean()
std_daily_return  = value_df['daily_return'].std()
sharpe_ratio = (mean_daily_return / std_daily_return) * np.sqrt(252)

# --- Max Drawdown ---
value_df['peak'] = value_df['value'].cummax()
value_df['drawdown'] = (value_df['value'] - value_df['peak']) / value_df['peak']
max_drawdown = value_df['drawdown'].min()

# --- Buy & Hold comparison ---
bh_final = CAPITAL * (df['Close'].iloc[-1] / df['Close'].iloc[0])
bh_cagr  = (bh_final / CAPITAL) ** (1/years) - 1
bh_returns = df['Close'].pct_change()
bh_sharpe  = (bh_returns.mean() / bh_returns.std()) * np.sqrt(252)
bh_cummax  = df['Close'].cummax()
bh_drawdown = ((df['Close'] - bh_cummax) / bh_cummax).min()

print("\n" + "="*55)
print(f"{'METRIC':<25}{'OUR STRATEGY':>15}{'BUY & HOLD':>15}")
print("="*55)
print(f"{'Final Value':<25}{'$'+format(final_value,',.0f'):>15}{'$'+format(bh_final,',.0f'):>15}")
print(f"{'Total Return':<25}{(final_value/CAPITAL-1)*100:>14.1f}%{(bh_final/CAPITAL-1)*100:>14.1f}%")
print(f"{'CAGR (yearly)':<25}{cagr*100:>14.1f}%{bh_cagr*100:>14.1f}%")
print(f"{'Sharpe Ratio':<25}{sharpe_ratio:>15.2f}{bh_sharpe:>15.2f}")
print(f"{'Max Drawdown':<25}{max_drawdown*100:>14.1f}%{bh_drawdown*100:>14.1f}%")
print("="*55)

# ============================================================
# STEP 4 — TRADE STATISTICS
# ============================================================

trades_df = pd.DataFrame(trade_log)
sells = trades_df[trades_df['action'] == 'SELL']

print(f"\n=== TRADE STATS ===")
print(f"Total round-trip trades: {len(sells)}")

if len(sells) > 0:
    winning = sells[sells['profit'] > 0]
    losing  = sells[sells['profit'] < 0]
    print(f"Win rate: {len(winning)/len(sells)*100:.1f}%")
    print(f"Average win:  ${winning['profit'].mean():,.2f}")
    print(f"Average loss: ${losing['profit'].mean():,.2f}")
    print(f"\nExit reasons:")
    print(sells['reason'].value_counts())

# ============================================================
# STEP 5 — VISUALIZE
# ============================================================

fig, axes = plt.subplots(2, 1, figsize=(14, 9))
fig.suptitle(f'{TICKER} — Fixed Strategy (40% position, 6% stop)', fontsize=14)

axes[0].plot(value_df.index, value_df['value'],
             color='green', linewidth=2, label='Our Strategy (Fixed)')
axes[0].plot(df.index, df['Close'] * (CAPITAL/df['Close'].iloc[0]),
             color='blue', linewidth=1.5, alpha=0.7, label='Buy & Hold')
axes[0].axhline(y=CAPITAL, color='gray', linewidth=1, linestyle='--')
axes[0].set_title('Portfolio Value: Fixed Strategy vs Buy & Hold')
axes[0].set_ylabel('Value ($)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].fill_between(value_df.index, value_df['drawdown']*100, 0,
                     color='red', alpha=0.4)
axes[1].set_title(f'Drawdown Over Time (Max: {max_drawdown*100:.1f}%)')
axes[1].set_ylabel('Drawdown (%)')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/backtest_fixed.png', dpi=150)
plt.close()

print("\nChart saved to data/backtest_fixed.png")
print("\n=== PHASE 4 STEP 1 COMPLETE ===")