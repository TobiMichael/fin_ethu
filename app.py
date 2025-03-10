import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pandas_datareader.data as web

# --------------------------------------#
# Streamlit App Configuration
# --------------------------------------#
st.set_page_config(page_title="Stock & Fed Funds Rate Analysis", layout="wide")

# App Title
st.title("Stock Analysis with Fed Funds Rate")

# --------------------------------------#
# User Input: Stock Ticker and Date Range
# --------------------------------------#
st.sidebar.header("Input Parameters")

# Get stock ticker from user
ticker = st.sidebar.text_input("Enter the stock ticker symbol (e.g., AAPL, VOO):", value="AAPL").upper()

# Get start date from user
start_date = st.sidebar.date_input("Start Date:", datetime(2023, 1, 1)).strftime('%Y-%m-%d')

# Get end date (current date)
end_date = datetime.today().strftime('%Y-%m-%d')

# --------------------------------------#
# Fetch and Process Stock Data
# --------------------------------------#
st.sidebar.write("Fetching stock data...")

api_key = "DEMO"  # Replace with your EOD API key
url = (
    f"https://eodhistoricaldata.com/api/eod/{ticker}"
    f"?api_token={api_key}&from={start_date}&to={end_date}&fmt=json"
)

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        # Convert JSON data into a DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values('date', inplace=True)
        df.set_index('date', inplace=True)
        
        # Resample daily data into monthly aggregated OHLC data
        monthly_df = df.resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        st.sidebar.success("Stock data fetched successfully!")
    else:
        st.sidebar.error("No stock data returned. Check the ticker symbol or date range.")
        monthly_df = pd.DataFrame()
else:
    st.sidebar.error(f"Error fetching stock data; HTTP Status Code: {response.status_code}")
    monthly_df = pd.DataFrame()

# --------------------------------------#
# Fetch and Process Fed Funds Rate Data
# --------------------------------------#
st.sidebar.write("Fetching Fed Funds Rate data...")

try:
    # Fetch Fed Funds Rate (FEDFUNDS) from FRED
    fed_data = web.DataReader('FEDFUNDS', 'fred', start_date, end_date)
    fed_monthly = fed_data.resample('M').mean()
    fed_monthly_aligned = fed_monthly.reindex(monthly_df.index, method='ffill')
    fed_monthly_aligned.fillna(method='bfill', inplace=True)
    st.sidebar.success("Fed Funds Rate data fetched successfully!")
except Exception as e:
    st.sidebar.error(f"Error fetching Fed Funds Rate data: {e}")
    fed_monthly_aligned = pd.DataFrame()

# --------------------------------------#
# Plotting the Data
# --------------------------------------#
if not monthly_df.empty and not fed_monthly_aligned.empty:
    st.sidebar.write("Generating chart...")

    # Create a simple line chart to display stock close prices
    st.line_chart(monthly_df['close'], use_container_width=True)

    # Overlay the Fed Funds Rate as a line chart
    st.line_chart(fed_monthly_aligned['FEDFUNDS'], use_container_width=True)
else:
    st.warning("Insufficient data: Stock data or Fed Funds Rate data is not available for the given date range.")


