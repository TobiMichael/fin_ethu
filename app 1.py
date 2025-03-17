import pandas as pd
import mplfinance as mpf
import requests
from io import StringIO  # Import StringIO from the io library
import streamlit as st
from matplotlib import pyplot as plt

# Streamlit app title
st.title("Apple Stock, Federal Reserve Rate, and Inflation Analysis (2000 - Present)")

# Replace 'YOUR_API_KEY' with your EOD Historical Data API key
API_KEY = 'DEMO'  # Replace with your actual API key
symbol = 'AAPL.US'
start_date = '2000-01-01'
end_date = '2025-03-17'

# Fetch EOD data
url = f'https://eodhistoricaldata.com/api/eod/{symbol}?from={start_date}&to={end_date}&api_token={API_KEY}&period=d'
response = requests.get(url)
data = response.text

# Convert the data to a DataFrame using StringIO
df = pd.read_csv(StringIO(data))
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Generate the candlestick chart
fig, ax_candles = plt.subplots(figsize=(12, 6))  # Create figure for candlestick chart
mpf.plot(df, type='candle', style='yahoo', ax=ax_candles)  # Plot candlestick chart
st.subheader("Candlestick Chart")
st.pyplot(fig)

# Generate the volume chart
fig, ax_volume = plt.subplots(figsize=(12, 4))  # Create a separate figure for volume
ax_volume.bar(df.index, df['Volume'], color='blue', width=1)
ax_volume.set_title("Volume Over Time")
ax_volume.set_ylabel("Volume")
ax_volume.set_xlabel("Date")
st.subheader("Volume Chart")
st.pyplot(fig)

# Fetch inflation rate data (example using a placeholder API or CSV file)
# Replace this with actual inflation data source
inflation_data = {
    "Date": ["2000-01-01", "2005-01-01", "2010-01-01", "2015-01-01", "2020-01-01", "2025-01-01"],
    "Inflation Rate (%)": [3.4, 2.8, 1.6, 0.1, 1.2, 2.3]
}
inflation_df = pd.DataFrame(inflation_data)
inflation_df['Date'] = pd.to_datetime(inflation_df['Date'])
inflation_df.set_index('Date', inplace=True)

# Generate the inflation rate chart
fig, ax_inflation = plt.subplots(figsize=(12, 4))  # Create a separate figure for inflation rate chart
ax_inflation.plot(inflation_df.index, inflation_df['Inflation Rate (%)'], color='green', linewidth=2)
ax_inflation.set_title("Inflation Rate Over Time")
ax_inflation.set_ylabel("Inflation Rate (%)")
ax_inflation.set_xlabel("Date")
st.subheader("Inflation Rate Chart")
st.pyplot(fig)
