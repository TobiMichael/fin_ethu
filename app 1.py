import pandas as pd
import mplfinance as mpf
import requests
from io import StringIO  # Import StringIO from the io library
import streamlit as st
from matplotlib import pyplot as plt

# Streamlit app title
st.title("Apple Stock Candlestick Chart (2021 - Present)")

# Replace 'YOUR_API_KEY' with your EOD Historical Data API key
API_KEY = 'DEMO'  # Replace with your actual API key
symbol = 'AAPL.US'
start_date = '2021-01-01'
end_date = '2025-03-17'

# Fetch EOD data
url = f'https://eodhistoricaldata.com/api/eod/{symbol}?from={start_date}&to={end_date}&api_token={API_KEY}&period=d'
response = requests.get(url)
data = response.text

# Convert the data to a DataFrame using StringIO
df = pd.read_csv(StringIO(data))
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Generate the candlestick plot with external axes
fig, ax_candles = plt.subplots(figsize=(12, 8))  # Create a figure and axes
mpf.plot(df, type='candle', style='yahoo', ax=ax_candles)  # Plot on the specified axes

# Render the plot in Streamlit
st.pyplot(fig)
