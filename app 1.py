import pandas as pd
import mplfinance as mpf
import requests
from io import StringIO
import streamlit as st
from matplotlib import pyplot as plt
from datetime import datetime

# Set the page configuration with title and layout
st.set_page_config(page_title="Finance Enthusiast", layout="wide")

# Fetching Federal Reserve rate data
def fetch_fed_rate_data():
    dates = pd.date_range(start='2000-01-01', end=datetime.now().strftime('2025-03-17'), freq='AS')
    rates = [6.5, 6.0, 1.75, 1.0, 2.0, 3.25, 0.0, 0.25, 0.5, 2.0, 2.25, 0.25, 
             0.1, 0.25, 0.75, 1.5, 2.5, 2.25, 4.5, 4.75, 5.0, 5.5, 5.0, 5.25, 5.5]

    if len(rates) < len(dates):
        rates.extend([None] * (len(dates) - len(rates)))

    data = {
        'Date': dates,
        'Rate': rates
    }

    return pd.DataFrame(data)

# Streamlit app title
st.title("Finance Enthusiast")

# Initialize session state for date range if it doesn't exist
if "start_date" not in st.session_state or "end_date" not in st.session_state:
    st.session_state.start_date = datetime(2000, 1, 1)
    st.session_state.end_date = datetime.now()

# Sidebar widget for user input
st.sidebar.title("Stock Ticker Input")
stock_ticker = st.sidebar.text_input("Enter Stock Ticker:", "AAPL")  # Default value is "AAPL"

# Get today's date dynamically
today = datetime.now()

# Single date range slider at the top of the screen
date_range = st.slider(
    "Select Date Range:",
    min_value=datetime(2000, 1, 1),
    max_value=today,
    value=(st.session_state.start_date, st.session_state.end_date),
    format="YYYY-MM-DD"
)

# Update session state with the selected range
st.session_state.start_date, st.session_state.end_date = date_range
start_date, end_date = st.session_state.start_date, st.session_state.end_date

# Fetch data using the stock ticker entered by the user
API_KEY = 'DEMO'  # Replace with your actual API key
url = f'https://eodhistoricaldata.com/api/eod/{stock_ticker}.US?from={start_date.strftime("%Y-%m-%d")}&to={end_date.strftime("%Y-%m-%d")}&api_token={API_KEY}&period=d'

response = requests.get(url)
data = response.text

# Convert the data to a DataFrame using StringIO
df = pd.read_csv(StringIO(data))
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Generate the candlestick chart
if not df.empty:
    fig, ax_candles = plt.subplots(figsize=(12, 6))  # Create figure for candlestick chart
    mpf.plot(df, type='candle', style='yahoo', ax=ax_candles)  # Plot candlestick chart
    st.subheader(f"{stock_ticker.upper()} Stock Candlestick Chart")
    st.pyplot(fig)
else:
    st.warning(f"No data available for the stock ticker: {stock_ticker.upper()}")

# Fetch and process Fed rate data
fed_data = fetch_fed_rate_data()
if not fed_data.empty:
    fed_data['Date'] = pd.to_datetime(fed_data['Date'])
    
    # Filter Fed rate data by the selected date range
    fed_data_filtered = fed_data[(fed_data['Date'] >= start_date) & (fed_data['Date'] <= end_date)]
    
    # Generate the Fed rate chart
    st.subheader("Federal Reserve Rate Chart")
    st.line_chart(fed_data_filtered.set_index('Date'))
