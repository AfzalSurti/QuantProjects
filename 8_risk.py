# ============================================================
# PHASE 5 — RISK MANAGER
# File: 08_risk.py
# Job: Stress test strategy against worst market periods
# ============================================================

import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TICKER       = "AAPL"
CAPITAL      = 10000
POSITION_PCT = 0.40
STOP_LOSS    = 0.06
TAKE_PROFIT  = 0.12

df = pd.read_csv(f"data/{TICKER}.csv", header=[0,1],
                 index_col=0, parse_dates=True)
df.columns   = [col[0] for col in df.columns]
df['Return'] = df['Close'].pct_change()

# ============================================================
# STEP 1 — Rebuild Signal and Run Simulation
# (same as Phase 4 — we need the daily_value data)
# ============================================================

df['SMA20']       = df['Close'].rolling(window=20).mean()
df['SMA50']       = df['Close'].rolling(window=50).mean()
df['Volume_SMA20']= df['Volume'].rolling(window=20).mean()
df['Volume_Ratio']= df['Volume'] / df['Volume_SMA20']

def calculate_rsi(prices, period=14):
    delta        = prices.diff()
    gains        = delta.copy()
    losses       = delta.copy()
    gains[gains < 0]   = 0
    losses[losses > 0] = 0
    losses       = abs(losses)
    avg_gain     = gains.rolling(window=period).mean()
    avg_loss     = losses.rolling(window=period).mean()
    rs           = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

df['RSI']    = calculate_rsi(df['Close'], period=14)

condition_trend  = df['SMA20'] > df['SMA50']
condition_volume = df['Volume_Ratio'] > 1.0
condition_rsi    = (df['RSI'] >= 50) & (df['RSI'] <= 70)

df['Signal'] = 0
df.loc[condition_trend & condition_volume & condition_rsi, 'Signal'] = 1
df.loc[(df['SMA20'] < df['SMA50']) & condition_volume, 'Signal'] = -1

# Run simulation
capital     = CAPITAL
position    = 0
entry_price = 0
trade_log   = []
daily_value = []

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
            position = 0; entry_price = 0

        elif price_change >= TAKE_PROFIT:
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital   += sell_value
            trade_log.append({'date': today, 'action': 'SELL',
                              'reason': 'TAKE PROFIT', 'price': price,
                              'shares': position, 'profit': profit,
                              'capital': capital})
            position = 0; entry_price = 0

        elif signal == -1:
            sell_value = position * price
            profit     = sell_value - (position * entry_price)
            capital   += sell_value
            trade_log.append({'date': today, 'action': 'SELL',
                              'reason': 'SIGNAL EXIT', 'price': price,
                              'shares': position, 'profit': profit,
                              'capital': capital})
            position = 0; entry_price = 0

    elif position == 0 and signal == 1:
        trade_capital = capital * POSITION_PCT
        shares        = int(trade_capital / price)
        if shares > 0:
            capital    -= shares * price
            position    = shares
            entry_price = price
            trade_log.append({'date': today, 'action': 'BUY',
                              'reason': 'SIGNAL ENTRY', 'price': price,
                              'shares': shares, 'profit': 0,
                              'capital': capital})

    total_value = capital + (position * price)
    daily_value.append({'date': today, 'value': total_value})

value_df               = pd.DataFrame(daily_value).set_index('date')
value_df['return']     = value_df['value'].pct_change()
value_df['peak']       = value_df['value'].cummax()
value_df['drawdown']   = (value_df['value'] - value_df['peak']) / value_df['peak']
df['BuyHold']          = CAPITAL * (df['Close'] / df['Close'].iloc[0])

print("Simulation rebuilt successfully")
print(f"Final portfolio value: ${value_df['value'].iloc[-1]:,.2f}")

# ============================================================
# STEP 2 — STRESS TEST FUNCTION
# ============================================================

def stress_test(name, start_date, end_date, value_df, df):
    
    print(f"\n{'='*55}")
    print(f"STRESS TEST: {name}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*55}")
    
    # Slice to the crisis period only
    strat  = value_df.loc[start_date:end_date, 'value']
    bh     = df.loc[start_date:end_date, 'BuyHold']
    signal = df.loc[start_date:end_date, 'Signal']
    
    if len(strat) == 0:
        print("No data for this period")
        return
    
    # Calculate returns during this period
    strat_return = (strat.iloc[-1] / strat.iloc[0] - 1) * 100
    bh_return    = (bh.iloc[-1]   / bh.iloc[0]   - 1) * 100
    
    # Worst single day for each
    strat_worst_day = value_df.loc[start_date:end_date, 'return'].min() * 100
    bh_worst_day    = df.loc[start_date:end_date, 'Return'].min() * 100
    
    # Drawdown during crisis
    strat_dd = value_df.loc[start_date:end_date, 'drawdown'].min() * 100
    
    # How many days was signal active (in market) during crisis
    days_in_market  = (signal == 1).sum()
    days_out_market = (signal != 1).sum()
    total_days      = len(signal)
    
    print(f"\n{'METRIC':<30}{'OUR STRATEGY':>15}{'BUY & HOLD':>15}")
    print(f"{'-'*60}")
    print(f"{'Period Return':<30}{strat_return:>14.1f}%{bh_return:>14.1f}%")
    print(f"{'Worst Single Day':<30}{strat_worst_day:>14.1f}%{bh_worst_day:>14.1f}%")
    print(f"{'Max Drawdown':<30}{strat_dd:>14.1f}%{'N/A':>15}")
    print(f"\n{'Signal Activity':<30}")
    print(f"  Days IN market:  {days_in_market} ({days_in_market/total_days*100:.0f}%)")
    print(f"  Days OUT of market: {days_out_market} ({days_out_market/total_days*100:.0f}%)")
    
    # Verdict
    print(f"\nVERDICT:")
    if strat_return > bh_return:
        diff = strat_return - bh_return
        print(f"✅ Strategy OUTPERFORMED Buy&Hold by {diff:.1f}%")
    else:
        diff = bh_return - strat_return
        print(f"⚠️  Strategy UNDERPERFORMED Buy&Hold by {diff:.1f}%")
    
    if strat_return > -10:
        print(f"✅ Strategy SURVIVED (loss < 10%)")
    elif strat_return > -20:
        print(f"⚠️  Strategy HURT (loss 10-20%) but survivable")
    else:
        print(f"❌ Strategy BADLY DAMAGED (loss > 20%)")
    
    return {
        'name': name,
        'strat_return': strat_return,
        'bh_return': bh_return,
        'strat_worst_day': strat_worst_day,
        'days_in_market_pct': days_in_market/total_days*100
    }

# ============================================================
# STEP 3 — RUN STRESS TESTS
# ============================================================

results = []

r1 = stress_test(
    "COVID CRASH",
    "2020-02-01",
    "2020-04-30",
    value_df, df
)

r2 = stress_test(
    "2022 BEAR MARKET",
    "2022-01-01",
    "2022-12-31",
    value_df, df
)

r3 = stress_test(
    "2018 Q4 SELLOFF",
    "2018-10-01",
    "2018-12-31",
    value_df, df
)

for r in [r1, r2, r3]:
    if r:
        results.append(r)
    
# ============================================================
# STEP 4 — ROLLING SHARPE RATIO
# Shows if strategy is consistently good or lucky
# ============================================================

window = 126  # 6 months of trading days

value_df['rolling_sharpe'] = (
    value_df['return']
    .rolling(window)
    .apply(lambda x: (x.mean() / x.std()) * np.sqrt(252)
           if x.std() > 0 else 0)
)

df['bh_return']         = df['Close'].pct_change()
df['bh_rolling_sharpe'] = (
    df['bh_return']
    .rolling(window)
    .apply(lambda x: (x.mean() / x.std()) * np.sqrt(252)
           if x.std() > 0 else 0)
)

print(f"\n=== ROLLING SHARPE STATS ===")
print(f"Our Strategy:")
print(f"  Mean:  {value_df['rolling_sharpe'].mean():.2f}")
print(f"  Min:   {value_df['rolling_sharpe'].min():.2f}")
print(f"  Max:   {value_df['rolling_sharpe'].max():.2f}")
print(f"  % time positive: {(value_df['rolling_sharpe']>0).mean()*100:.0f}%")


# ============================================================
# STEP 5 — FULL RISK SUMMARY
# ============================================================

years        = (df.index[-1] - df.index[0]).days / 365.25
final_value  = value_df['value'].iloc[-1]
cagr         = (final_value / CAPITAL) ** (1/years) - 1
max_drawdown = value_df['drawdown'].min()
calmar       = cagr / abs(max_drawdown)

bh_cagr      = (df['BuyHold'].iloc[-1] / CAPITAL) ** (1/years) - 1
bh_dd        = ((df['BuyHold'] - df['BuyHold'].cummax())
                / df['BuyHold'].cummax()).min()
bh_calmar    = bh_cagr / abs(bh_dd)

print(f"\n{'='*55}")
print(f"COMPLETE RISK PROFILE")
print(f"{'='*55}")
print(f"{'METRIC':<28}{'OUR STRATEGY':>13}{'BUY & HOLD':>13}")
print(f"{'-'*55}")
print(f"{'CAGR':<28}{cagr*100:>12.1f}%{bh_cagr*100:>12.1f}%")
print(f"{'Max Drawdown':<28}{max_drawdown*100:>12.1f}%{bh_dd*100:>12.1f}%")
print(f"{'Calmar Ratio':<28}{calmar:>13.2f}{bh_calmar:>13.2f}")
print(f"{'Sharpe Ratio':<28}"
      f"{(value_df['return'].mean()/value_df['return'].std())*np.sqrt(252):>13.2f}"
      f"{(df['bh_return'].mean()/df['bh_return'].std())*np.sqrt(252):>13.2f}")
print(f"{'Recovery ability':<28}"
      f"{'High (small DD)':>13}"
      f"{'Low (big DD)':>13}")
print(f"{'='*55}")


# ============================================================
# STEP 6 — VISUALIZATION
# ============================================================

fig, axes = plt.subplots(4, 1, figsize=(14, 16))
fig.suptitle(f'{TICKER} — Phase 5: Risk Analysis', fontsize=14)

# Chart 1: Portfolio value with crisis zones highlighted
axes[0].plot(value_df.index, value_df['value'],
             color='green', linewidth=2, label='Our Strategy')
axes[0].plot(df.index, df['BuyHold'],
             color='blue', linewidth=1.5, alpha=0.6, label='Buy & Hold')

# Highlight crisis periods
crises = [
    ("2018-10-01", "2018-12-31", "2018 Selloff"),
    ("2020-02-01", "2020-04-30", "COVID Crash"),
    ("2022-01-01", "2022-12-31", "2022 Bear"),
]
colors_crisis = ['orange', 'red', 'purple']

for (start, end, label), color in zip(crises, colors_crisis):
    axes[0].axvspan(start, end, alpha=0.15,
                    color=color, label=label)

axes[0].axhline(y=CAPITAL, color='gray', linewidth=1, linestyle='--')
axes[0].set_title('Portfolio Value with Crisis Periods Highlighted')
axes[0].set_ylabel('Value ($)')
axes[0].legend(loc='upper left', fontsize=8)
axes[0].grid(True, alpha=0.3)

# Chart 2: Drawdown
axes[1].fill_between(value_df.index, value_df['drawdown']*100, 0,
                     color='red', alpha=0.5, label='Strategy Drawdown')
for (start, end, label), color in zip(crises, colors_crisis):
    axes[1].axvspan(start, end, alpha=0.15, color=color)
axes[1].set_title(f'Drawdown Over Time (Max: {max_drawdown*100:.1f}%)')
axes[1].set_ylabel('Drawdown (%)')
axes[1].grid(True, alpha=0.3)

# Chart 3: Rolling Sharpe
axes[2].plot(value_df.index, value_df['rolling_sharpe'],
             color='green', linewidth=1.5, label='Strategy Rolling Sharpe')
axes[2].plot(df.index, df['bh_rolling_sharpe'],
             color='blue', linewidth=1, alpha=0.6, label='B&H Rolling Sharpe')
axes[2].axhline(y=0, color='black', linewidth=1, linestyle='--')
axes[2].axhline(y=1, color='green', linewidth=1,
                linestyle=':', alpha=0.7, label='Sharpe = 1.0')
for (start, end, label), color in zip(crises, colors_crisis):
    axes[2].axvspan(start, end, alpha=0.15, color=color)
axes[2].set_title('Rolling 6-Month Sharpe Ratio')
axes[2].set_ylabel('Sharpe')
axes[2].legend(loc='upper right', fontsize=8)
axes[2].grid(True, alpha=0.3)

# Chart 4: Signal activity
axes[3].fill_between(df.index, 0, df['Signal'],
                     where=(df['Signal'] == 1),
                     alpha=0.5, color='green', label='In Market (BUY)')
axes[3].fill_between(df.index, df['Signal'], 0,
                     where=(df['Signal'] == -1),
                     alpha=0.5, color='red', label='SELL Signal')
for (start, end, label), color in zip(crises, colors_crisis):
    axes[3].axvspan(start, end, alpha=0.15, color=color)
axes[3].set_title('Signal Activity During Crisis Periods')
axes[3].set_ylabel('Signal')
axes[3].set_yticks([-1, 0, 1])
axes[3].legend(loc='upper right', fontsize=8)
axes[3].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/risk_analysis.png', dpi=150)
plt.close()

print("\nChart saved to data/risk_analysis.png")
print("\n=== PHASE 5 COMPLETE ===")