import yfinance as yf
import pandas as pd
import os

TICKER="AAPL" # to fetch data for Apple Inc. You can change this to any ticker symbol you want.
START="2018-01-01"# Adjusted start date to ensure we have enough historical data for training
END="2024-01-01" # Adjusted end date to ensure we have data up to the current date

def fetch_data(ticker,start,end):

    print(f"fetching data for  {ticker} form {start} to {end}")

    df=yf.download(ticker,start=start,end=end,auto_adjust=True)

    if df.empty:
        print(f"No data found for {ticker} from {start} to {end}. Please check the ticker symbol and date range.")

        return None
    
    print(f"Download {len(df)} rows of data")

    print(f"data range : {df.index[0]} to {df.index[-1]}")

    print(f"first 5 rows of data : \n{df.head()}")

    os.makedirs("data",exist_ok=True)
    filepath=f"data/{ticker}.csv"
    df.to_csv(filepath)

    print(f"data saved to {filepath}")
    print("done")

    return df

df=fetch_data(TICKER,START,END)
    