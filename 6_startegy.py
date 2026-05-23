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

