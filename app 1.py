import pandas as pd
import mplfinance as mpf
import requests
from io import StringIO  # Import StringIO from the io library
import streamlit as st
from matplotlib import pyplot as plt
from datetime import datetime

# Streamlit app title
st.title("Apple Stock, Federal Reserve Rate, and Inflation Analysis")

# Single date range slider at the top of the screen
date_range = st.slider(
    "Select Date Range:",
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2025, 1, 1),
    value=(datetime(2000, 1, 1), datetime(2025, 1, 1)),
    format="YYYY-MM-DD"
)
start_date, end_date = date_range

# Replace 'YOUR_API_KEY' with your EOD Historical Data API key
API_KEY = 'DEMO'  # Replace with your actual API key
symbol = 'AAPL.US'

# Fetch EOD data
url = f'https://eodhistoricaldata.com/api/eod/{symbol}?from={start_date.strftime("%Y-%m-%d")}&to={end_date.strftime("%Y-%m-%d")}&api_token={API_KEY}&period=d'
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

# Fetch Federal Reserve rate data (example using FRED API)
fred_api_key = 'YOUR_FRED_API_KEY'  # Replace with your FRED API key
fred_url = f'https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={fred_api_key}&file_type=json'
fred_response = requests.get(fred_url).json()

# Convert FRED data to DataFrame
if 'observations' in fred_response:
    fred_data = pd.DataFrame(fred_response['observations'])
    fred_data['date'] = pd.to_datetime(fred_data['date'])
    fred_data['value'] = pd.to_numeric(fred_data['value'])
    fred_data.set_index('date', inplace=True)

    # Filter data by selected date range
    fred_data = fred_data[(fred_data.index >= start_date) & (fred_data.index <= end_date)]

    # Generate the Fed rate chart
    fig, ax_fed = plt.subplots(figsize=(12, 4))  # Create a separate figure for Fed rate chart
    ax_fed.plot(fred_data.index, fred_data['value'], color='red', linewidth=2)
    ax_fed.set_title("Federal Reserve Rate Cuts Over Time")
    ax_fed.set_ylabel("Interest Rate (%)")
    ax_fed.set_xlabel("Date")
    st.subheader("Federal Reserve Rate Chart")
    st.pyplot(fig)

# Fetch inflation rate data (example using a placeholder dataset)
inflation_data = {
    "Date": ["2000-01-01", "2005-01-01", "2010-01-01", "2015-01-01", "2020-01-01", "2025-01-01"],
    "Inflation Rate (%)": [3.4, 2.8, 1.6, 0.1, 1.2, 2.3]
}
inflation_df = pd.DataFrame(inflation_data)
inflation_df['Date'] = pd.to_datetime(inflation_df['Date'])
inflation_df.set_index('Date', inplace=True)

# Filter inflation data by selected date range
inflation_df = inflation_df[(inflation_df.index >= start_date) & (inflation_df.index <= end_date)]

# Generate the inflation rate chart
fig, ax_inflation = plt.subplots(figsize=(12, 4))  # Create a separate figure for inflation rate chart
ax_inflation.plot(inflation_df.index, inflation_df['Inflation Rate (%)'], color='green', linewidth=2)
ax_inflation.set_title("Inflation Rate Over Time")
ax_inflation.set_ylabel("Inflation Rate (%)")
ax_inflation.set_xlabel("Date")
st.subheader("Inflation Rate Chart")
st.pyplot(fig)

