# ============================================================
# PHASE 6 — PAPER TRADING
# File: 09_paper_trade.py
# Job: Run strategy on live market data with fake money
# ============================================================

import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import os
import yfinance as yf 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Load API keys from .env file
load_dotenv()

API_KEY    = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
BASE_URL   = os.getenv('BASE_URL')

# Connect to Alpaca
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

# Strategy parameters
TICKER       = "AAPL"
POSITION_PCT = 0.40
STOP_LOSS    = 0.06
TAKE_PROFIT  = 0.12

# ============================================================
# STEP 1 — TEST CONNECTION
# ============================================================

def test_connection():
    try:
        account = api.get_account()
        print("=== ACCOUNT STATUS ===")
        print(f"Account status:    {account.status}")
        print(f"Buying power:      ${float(account.buying_power):,.2f}")
        print(f"Portfolio value:   ${float(account.portfolio_value):,.2f}")
        print(f"Cash:              ${float(account.cash):,.2f}")
        print(f"Paper trading:     YES — no real money")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

# ============================================================
# STEP 2 — GET LIVE SIGNAL
# ============================================================

def get_signal():
    print(f"\n=== CALCULATING LIVE SIGNAL ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Download recent data — need 60 days for SMA50
    end   = datetime.now()
    start = end - timedelta(days=120)

    df = yf.download(
        TICKER,
        start=start.strftime('%Y-%m-%d'),
        end=end.strftime('%Y-%m-%d'),
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        print("No data downloaded")
        return 0

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # Calculate indicators
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['Volume_SMA20'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA20']

    # RSI
    delta    = df['Close'].diff()
    gains    = delta.copy()
    losses   = delta.copy()
    gains[gains < 0]   = 0
    losses[losses > 0] = 0
    losses   = abs(losses)
    avg_gain = gains.rolling(window=14).mean()
    avg_loss = losses.rolling(window=14).mean()
    rs       = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Get latest values
    latest = df.iloc[-1]

    print(f"\nLatest data ({df.index[-1].date()}):")
    print(f"  Close:        ${float(latest['Close']):.2f}")
    print(f"  SMA20:        ${float(latest['SMA20']):.2f}")
    print(f"  SMA50:        ${float(latest['SMA50']):.2f}")
    print(f"  Volume Ratio: {float(latest['Volume_Ratio']):.2f}x")
    print(f"  RSI:          {float(latest['RSI']):.1f}")

    # Check conditions
    condition_trend  = latest['SMA20'] > latest['SMA50']
    condition_volume = latest['Volume_Ratio'] > 1.0
    condition_rsi    = 50 <= latest['RSI'] <= 70

    print(f"\nCondition Check:")
    print(f"  Trend  (SMA20>SMA50):    {'✅' if condition_trend  else '❌'}")
    print(f"  Volume (ratio>1.0):      {'✅' if condition_volume else '❌'}")
    print(f"  RSI    (50-70):          {'✅' if condition_rsi    else '❌'}")

    if condition_trend and condition_volume and condition_rsi:
        print(f"\n🟢 SIGNAL = BUY")
        return 1
    elif not condition_trend and condition_volume:
        print(f"\n🔴 SIGNAL = SELL/STAY OUT")
        return -1
    else:
        print(f"\n⚪ SIGNAL = HOLD/WAIT")
        return 0

# ============================================================
# STEP 3 — CHECK CURRENT POSITION
# ============================================================

def get_position():
    try:
        position = api.get_position(TICKER)
        shares = int(position.qty)
        entry  = float(position.avg_entry_price)
        value  = float(position.market_value)
        pnl    = float(position.unrealized_pl)
        pnl_pct = float(position.unrealized_plpc) * 100

        print(f"\n=== CURRENT POSITION ===")
        print(f"  Shares held:     {shares}")
        print(f"  Entry price:     ${entry:.2f}")
        print(f"  Current value:   ${value:.2f}")
        print(f"  Unrealized PnL:  ${pnl:.2f} ({pnl_pct:.2f}%)")
        return shares, entry, pnl_pct
    except:
        print(f"\n=== CURRENT POSITION ===")
        print(f"  No open position in {TICKER}")
        return 0, 0, 0

# ============================================================
# STEP 4 — EXECUTE TRADES
# ============================================================

def buy_stock():
    try:
        account       = api.get_account()
        buying_power  = float(account.buying_power)
        trade_capital = buying_power * POSITION_PCT

        # Get current price
        quote  = api.get_latest_trade(TICKER)
        price  = quote.price
        shares = int(trade_capital / price)

        if shares < 1:
            print("Not enough buying power for 1 share")
            return False

        # Place market order
        api.submit_order(
            symbol     = TICKER,
            qty        = shares,
            side       = 'buy',
            type       = 'market',
            time_in_force = 'day'
        )

        print(f"\n✅ BUY ORDER PLACED")
        print(f"   Symbol: {TICKER}")
        print(f"   Shares: {shares}")
        print(f"   Approx value: ${shares * price:,.2f}")
        return True

    except Exception as e:
        print(f"Buy order failed: {e}")
        return False

def sell_stock(reason="SIGNAL EXIT"):
    try:
        position = api.get_position(TICKER)
        shares   = int(position.qty)

        api.submit_order(
            symbol        = TICKER,
            qty           = shares,
            side          = 'sell',
            type          = 'market',
            time_in_force = 'day'
        )

        print(f"\n🔴 SELL ORDER PLACED")
        print(f"   Symbol: {TICKER}")
        print(f"   Shares: {shares}")
        print(f"   Reason: {reason}")
        return True

    except Exception as e:
        print(f"Sell order failed: {e}")
        return False

# ============================================================
# STEP 5 — MAIN STRATEGY LOOP
# ============================================================

def run_strategy():
    print("\n" + "="*50)
    print("PHASE 6 — PAPER TRADING LIVE")
    print("="*50)

    # Test connection first
    if not test_connection():
        return

    # Get signal
    signal = get_signal()

    # Check current position
    shares, entry_price, pnl_pct = get_position()

    print(f"\n=== STRATEGY DECISION ===")

    # If we hold a position — check exits
    if shares > 0:
        if pnl_pct <= -STOP_LOSS * 100:
            print(f"Stop loss triggered ({pnl_pct:.2f}%)")
            sell_stock("STOP LOSS")

        elif pnl_pct >= TAKE_PROFIT * 100:
            print(f"Take profit triggered ({pnl_pct:.2f}%)")
            sell_stock("TAKE PROFIT")

        elif signal == -1:
            print(f"Signal says exit")
            sell_stock("SIGNAL EXIT")

        else:
            print(f"Holding position — PnL: {pnl_pct:.2f}%")
            print(f"Stop loss at: -{STOP_LOSS*100}%")
            print(f"Take profit at: +{TAKE_PROFIT*100}%")

    # If no position — check entry
    elif shares == 0:
        if signal == 1:
            print(f"Signal says BUY — placing order")
            buy_stock()
        else:
            print(f"No position. Signal not active. Waiting.")

    # Summary
    print(f"\n=== RUN COMPLETE ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Next run: tomorrow before market open")

# ============================================================
# RUN IT
# ============================================================

run_strategy()