import pandas as pd
import mplfinance as mpf
import requests
from io import StringIO  # Import StringIO from the io library
from matplotlib import pyplot as plt
from datetime import datetime

# User-defined date range
start_date = datetime(2000, 1, 1)
end_date = datetime(2025, 1, 1)

# Fetch Apple stock data from EOD Historical Data API
API_KEY = 'DEMO'  # Replace with your actual API key
symbol = 'AAPL.US'
url = f'https://eodhistoricaldata.com/api/eod/{symbol}?from={start_date.strftime("%Y-%m-%d")}&to={end_date.strftime("%Y-%m-%d")}&api_token={API_KEY}&period=d'
response = requests.get(url)
data = response.text

# Convert the stock data to a DataFrame
df = pd.read_csv(StringIO(data))
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Plot the candlestick chart
fig, ax_candles = plt.subplots(figsize=(12, 6))  # Create a figure for the candlestick chart
mpf.plot(df, type='candle', style='yahoo', ax=ax_candles)  # Plot candlestick chart
ax_candles.set_title("Apple Stock Candlestick Chart")
plt.show()

# Scrape Federal Reserve rate data from a reliable source
fed_rate_url = "https://www.macrotrends.net/2015/fed-funds-rate-historical-chart"  # Example webpage
tables = pd.read_html(fed_rate_url)  # Fetch all tables on the webpage
fed_rate_df = tables[0]  # Assume the first table contains the data we need

# Process the Fed rate data
fed_rate_df.columns = ["Date", "Fed Rate (%)"]  # Rename columns
fed_rate_df["Date"] = pd.to_datetime(fed_rate_df["Date"])  # Convert Date to datetime
fed_rate_df.set_index("Date", inplace=True)

# Filter the Fed rate data by the selected date range
fed_rate_filtered = fed_rate_df[(fed_rate_df.index >= start_date) & (fed_rate_df.index <= end_date)]

# Plot the Fed rate chart
fig, ax_fed = plt.subplots(figsize=(12, 4))
ax_fed.plot(fed_rate_filtered.index, fed_rate_filtered["Fed Rate (%)"], color="red", linewidth=2)
ax_fed.set_title("Federal Reserve Rate Cuts Over Time")
ax_fed.set_ylabel("Interest Rate (%)")
ax_fed.set_xlabel("Date")
plt.show()

# Placeholder inflation rate data (replace with actual data if available)
inflation_data = {
    "Date": ["2000-01-01", "2005-01-01", "2010-01-01", "2015-01-01", "2020-01-01", "2025-01-01"],
    "Inflation Rate (%)": [3.4, 2.8, 1.6, 0.1, 1.2, 2.3]
}
inflation_df = pd.DataFrame(inflation_data)
inflation_df["Date"] = pd.to_datetime(inflation_df["Date"])
inflation_df.set_index("Date", inplace=True)

# Filter the inflation data by the selected date range
inflation_filtered = inflation_df[(inflation_df.index >= start_date) & (inflation_df.index <= end_date)]

# Plot the inflation rate chart
fig, ax_inflation = plt.subplots(figsize=(12, 4))
ax_inflation.plot(inflation_filtered.index, inflation_filtered["Inflation Rate (%)"], color="green", linewidth=2)
ax_inflation.set_title("Inflation Rate Over Time")
ax_inflation.set_ylabel("Inflation Rate (%)")
ax_inflation.set_xlabel("Date")
plt.show()
