import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TICKER="AAPL"

#step -1  - load data

df=pd.read_csv(f"data/{TICKER}.csv",header=[0,1],index_col=0,parse_dates=True)

print("raw columns after loading:")
print(df.columns)

df.columns=[col[0] for col in df.columns]

print("columns after cleaning")
print(df.columns.tolist())
print(f"\nshape: {df.shape}")
print(df.head(3))

# step -2 check data quality

print("missing values")
print(df.isnull().sum())

#step -3 - claculate daily returns

df['Return']=df['Close'].pct_change()

# pct_change() does ; today's price - yesterday's price / yesterday's price

print("daily returns")
print(df['Return'].describe()) # what is a diff in a head() and describe() method? - head() shows the first few rows of the data, while describe() provides summary statistics for the specified column, such as count, mean, std, min, 25%, 50%, 75%, and max values.

# step -4 find the crash

print("crash days")
print(df['Return'].nsmallest(5)) # nsmallest() method is used to find the n smallest values in a Series. In this case, it is used to find the 5 smallest daily returns, which can indicate potential crash days.

print("best days")
print(df['Return'].nlargest(5)) # nlargest() method is used to find the n largest values in a Series. In this case, it is used to find the 5 largest daily returns, which can indicate potential best days for the stock.


# step -5 visualise everything

fig,axes=plt.subplots(3,1,figsize=(14,10)) # creates a figure with 3 subplots arranged in a single column (3 rows, 1 column) and sets the overall size of the figure to 10 inches wide and 15 inches tall.
fig.suptitle(f'{TICKER} Market Data Analysis 2018-2024',fontsize=16) # sets a title for the entire figure, which will be displayed at the top of the figure. The title includes the ticker symbol and the date range of the data being analyzed.

#chart 1 - closing price

axes[0].plot(df.index,df['Close'],color='blue',linewidth=1) # plots the closing price of the stock over time. The x-axis represents the date (df.index), and the y-axis represents the closing price (df['Close']). The line is colored blue and has a width of 1.
axes[0].set_title('Close price (Adjusted)',fontsize=12) # sets the title for the first subplot, which describes the data being plotted (closing price).
axes[0].set_ylabel('Price($)',fontsize=10) # sets the label for the y-axis of the first subplot, indicating that the values represent price in dollars.
axes[0].grid(True,alpha=0.3) # adds a grid to the first subplot with a specified transparency (alpha=0.3).

#chart 2 - volume

axes[1].bar(df.index,df['Volume'],color='orange',width=1) # creates a bar chart to visualize the trading volume of the stock over time. The x-axis represents the date (df.index), and the y-axis represents the trading volume (df['Volume']). The bars are colored orange and have a width of 1.
axes[1].set_title('Trading Volume',fontsize=12) # sets the title for the second subplot, which describes the data being plotted (trading volume).
axes[1].set_ylabel('Volume',fontsize=10) # sets the label for the y-axis of the second subplot, indicating that the values represent trading volume.
axes[1].grid(True,alpha=0.3) 

#chart 3 - daily returns
# positive - green, negative - red

colors=['green' if r>0 else 'red' for r in df['Return']]
axes[2].bar(df.index,df['Return'],color=colors,alpha=0.6,width=1) # creates a bar chart to visualize the daily returns of the stock over time. The x-axis represents the date (df.index), and the y-axis represents the daily returns (df['Return']). The bars are colored green for positive returns and red for negative returns, with a width of 1.
axes[2].axhline(y=0,color='black',linewidth=0.8)
axes[2].set_title('Daily Returns',fontsize=12) # sets the title for the third subplot, which describes the data being plotted (daily returns).
axes[2].set_ylabel('Return',fontsize=10) # sets the label for the y-axis of the third subplot, indicating that the values represent daily returns.
axes[2].grid(True,alpha=0.3)

plt.tight_layout() # adjusts the spacing between the subplots to prevent overlap and ensure that the titles, labels, and other elements are displayed clearly without overlapping each other. It helps improve the overall appearance of the figure by optimizing the layout of the subplots.   
plt.savefig('data/exploration.png',dpi=150) # what is a dpi? - dpi stands for "dots per inch" and is a measure of the resolution of an image. In this context, setting dpi=150 means that the saved image will have a resolution of 150 dots per inch, which can affect the quality and clarity of the image when viewed or printed.
plt.show()