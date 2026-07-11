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


# ============================================================
# STEP 2 — STRATEGY SIMULATOR
# This is the heart of the strategy
# We simulate every single trade day by day
# ============================================================

# Storage for tracking everything
capital      = CAPITAL    # current capital — changes every trade
position     = 0          # shares currently held
entry_price  = 0          # price we bought at
trade_log    = []         # record of every trade

# We go through every single day one by one
for i in range(1, len(df)):
    
    today      = df.index[i]
    price      = df['Close'].iloc[i]
    signal     = df['Signal'].iloc[i-1]  # yesterday's signal
    
    # ── IF WE ARE CURRENTLY IN A TRADE ──────────────────────
    if position > 0:
        
        # Calculate how much price moved since we bought
        price_change = (price - entry_price) / entry_price
        
        # Check stop loss — did we lose too much?
        if price_change <= -STOP_LOSS:
            
            # SELL — stop loss triggered
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital    += sell_value
            
            trade_log.append({
                'date'      : today,
                'action'    : 'SELL',
                'reason'    : 'STOP LOSS',
                'price'     : price,
                'shares'    : position,
                'profit'    : profit,
                'capital'   : capital
            })
            
            position    = 0
            entry_price = 0
        
        # Check take profit — did we gain enough?
        elif price_change >= TAKE_PROFIT:
            
            # SELL — take profit triggered
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital    += sell_value
            
            trade_log.append({
                'date'      : today,
                'action'    : 'SELL',
                'reason'    : 'TAKE PROFIT',
                'price'     : price,
                'shares'    : position,
                'profit'    : profit,
                'capital'   : capital
            })
            
            position    = 0
            entry_price = 0
        
        # Check signal flip — did trend reverse?
        elif signal == -1:
            
            # SELL — signal says exit
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital    += sell_value
            
            trade_log.append({
                'date'      : today,
                'action'    : 'SELL',
                'reason'    : 'SIGNAL EXIT',
                'price'     : price,
                'shares'    : position,
                'profit'    : profit,
                'capital'   : capital
            })
            
            position    = 0
            entry_price = 0
    
    # ── IF WE ARE NOT IN A TRADE ─────────────────────────────
    elif position == 0 and signal == 1:
        
        # BUY — signal says enter
        trade_capital = capital * POSITION_PCT  # 10% of current capital
        shares        = int(trade_capital / price)  # whole shares only
        
        if shares > 0:
            cost          = shares * price
            capital      -= cost       # subtract from available capital
            position      = shares
            entry_price   = price
            
            trade_log.append({
                'date'      : today,
                'action'    : 'BUY',
                'reason'    : 'SIGNAL ENTRY',
                'price'     : price,
                'shares'    : shares,
                'profit'    : 0,
                'capital'   : capital
            })

print(f"\nSimulation complete")
print(f"Total trades: {len(trade_log)}")

# ============================================================
# STEP 3 — ANALYZE RESULTS
# ============================================================

trades_df = pd.DataFrame(trade_log)

if len(trades_df) == 0:
    print("No trades were made — check signal")
else:
    # Separate buys and sells
    sells = trades_df[trades_df['action'] == 'SELL']
    buys  = trades_df[trades_df['action'] == 'BUY']
    
    print("\n=== TRADE SUMMARY ===")
    print(f"Total trades (round trips): {len(sells)}")
    print(f"Final capital:  ${trades_df['capital'].iloc[-1]:,.2f}")
    print(f"Starting capital: ${CAPITAL:,.2f}")
    print(f"Total profit:   ${trades_df['capital'].iloc[-1] - CAPITAL:,.2f}")
    print(f"Total return:   {((trades_df['capital'].iloc[-1] / CAPITAL) - 1) * 100:.1f}%")
    
    # Exit reason breakdown
    print("\n=== EXIT REASONS ===")
    print(sells['reason'].value_counts())
    
    # Win/loss analysis
    winning_trades = sells[sells['profit'] > 0]
    losing_trades  = sells[sells['profit'] < 0]
    
    print("\n=== WIN/LOSS ANALYSIS ===")
    print(f"Winning trades: {len(winning_trades)} ({len(winning_trades)/len(sells)*100:.1f}%)")
    print(f"Losing trades:  {len(losing_trades)} ({len(losing_trades)/len(sells)*100:.1f}%)")
    print(f"Average win:    ${winning_trades['profit'].mean():,.2f}")
    print(f"Average loss:   ${losing_trades['profit'].mean():,.2f}")
    
    if len(losing_trades) > 0:
        rr = abs(winning_trades['profit'].mean() / losing_trades['profit'].mean())
        print(f"Risk/reward:    {rr:.2f}:1")
    
    # Show last 10 trades
    print("\n=== LAST 10 TRADES ===")
    print(trades_df.tail(10).to_string())

# ============================================================
# STEP 4 — TRACK CAPITAL OVER TIME
# ============================================================

# Build daily capital curve
capital_curve = []
current_cap   = CAPITAL

for i in range(len(df)):
    date  = df.index[i]
    price = df['Close'].iloc[i]
    
    # Find if there was a trade on this date
    day_trades = trades_df[trades_df['date'] == date] if len(trades_df) > 0 else pd.DataFrame()
    
    if len(day_trades) > 0:
        current_cap = day_trades['capital'].iloc[-1]
    
    # If holding position — mark to market
    # (what is portfolio worth RIGHT NOW)
    if position > 0 and entry_price > 0:
        unrealized = position * price
        total_value = current_cap + unrealized
    else:
        total_value = current_cap
    
    capital_curve.append({
        'date'  : date,
        'value' : total_value
    })

curve_df = pd.DataFrame(capital_curve).set_index('date')

# Buy and hold comparison
df['BuyHold'] = CAPITAL * (df['Close'] / df['Close'].iloc[0])

print("\n=== CAPITAL CURVE ===")
print(f"Start:  ${curve_df['value'].iloc[0]:,.2f}")
print(f"End:    ${curve_df['value'].iloc[-1]:,.2f}")
print(f"Max:    ${curve_df['value'].max():,.2f}")
print(f"Min:    ${curve_df['value'].min():,.2f}")

# ============================================================
# STEP 5 — VISUALIZE STRATEGY PERFORMANCE
# ============================================================

fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle(f'{TICKER} — Strategy Performance vs Buy & Hold', fontsize=14)

# Chart 1: Capital curve vs buy and hold
axes[0].plot(curve_df.index, curve_df['value'],
             color='green', linewidth=2, label='Our Strategy')
axes[0].plot(df.index, df['BuyHold'],
             color='blue', linewidth=1.5,
             alpha=0.7, label='Buy & Hold')
axes[0].axhline(y=CAPITAL, color='gray',
                linewidth=1, linestyle='--', label='Starting capital')
axes[0].set_title('Portfolio Value Over Time')
axes[0].set_ylabel('Portfolio Value ($)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Chart 2: Individual trade profits
if len(trades_df) > 0:
    sells = trades_df[trades_df['action'] == 'SELL']
    colors = ['green' if p > 0 else 'red' for p in sells['profit']]
    axes[1].bar(range(len(sells)), sells['profit'],
                color=colors, alpha=0.7)
    axes[1].axhline(y=0, color='black', linewidth=1)
    axes[1].set_title('Individual Trade Profits ($)')
    axes[1].set_ylabel('Profit per Trade ($)')
    axes[1].set_xlabel('Trade Number')
    axes[1].grid(True, alpha=0.3)

# Chart 3: Price with buy/sell markers
axes[2].plot(df.index, df['Close'],
             color='blue', linewidth=1, alpha=0.6, label='Price')

if len(trades_df) > 0:
    buy_trades  = trades_df[trades_df['action'] == 'BUY']
    sell_trades = trades_df[trades_df['action'] == 'SELL']
    
    # Plot buy markers
    for _, trade in buy_trades.iterrows():
        if trade['date'] in df.index:
            axes[2].scatter(trade['date'], trade['price'],
                          color='green', marker='^',
                          s=100, zorder=5)
    
    # Plot sell markers
    for _, trade in sell_trades.iterrows():
        if trade['date'] in df.index:
            color = 'red' if trade['profit'] < 0 else 'lime'
            axes[2].scatter(trade['date'], trade['price'],
                          color=color, marker='v',
                          s=100, zorder=5)

axes[2].set_title('Price Chart with Trade Entries (▲) and Exits (▼)')
axes[2].set_ylabel('Price ($)')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/strategy_performance.png', dpi=150)
plt.close()

print("\nChart saved to data/strategy_performance.png")
print("\n=== PHASE 3 COMPLETE ===")