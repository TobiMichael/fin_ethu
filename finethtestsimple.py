import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz # Import pytz for timezone handling

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Apply custom CSS for styling
st.markdown(
    """
    <style>
    body {
        color: #333;
        background-color: #f0f2f6;
    }
    .stPlot {
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    /* Style for the suggested ticker display */
    .suggested-ticker {
        background-color: #e9e9e9;
        padding: 8px;
        border-radius: 4px;
        margin-top: 10px;
        font-family: monospace;
        font-size: 1em;
        border: 1px solid #ccc;
        word-break: break-all; /* Prevent long tickers/names from overflowing */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_up = up.rolling(window).mean()
    average_down = down.rolling(window).mean()
    # Avoid division by zero in rs calculation
    # Replace 0 with a very small number (e.g., 1e-9) to prevent division by zero
    rs = average_up / average_down.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Provided function to attempt ticker lookup by potential name/ticker
def find_ticker_and_name(query):
    """Attempts to find a ticker and company name from a query string using yfinance."""
    if not query:
        return None, None

    # Try treating the query as a direct ticker first
    ticker_obj = yf.Ticker(query.upper())
    try:
        # Fetch info to validate the ticker and get the name
        # Checking for 'regularMarketPrice' or 'marketCap' is a good way to see if the ticker is valid and has data
        info = ticker_obj.info
        if info and (info.get('regularMarketPrice') is not None or info.get('marketCap') is not None):
             # If valid, return the ticker and its long name
             return query.upper(), info.get('longName', query.upper())
        else:
             # If direct ticker didn't work or no price/marketCap info, it might be a name (though yfinance lookup by name is unreliable)
             pass # Proceeding here won't magically make name search work well with yfinance
    except Exception as e:
        # print(f"Direct ticker lookup failed for {query}: {e}") # Optional: for debugging
        pass # It's likely not a direct valid ticker, might be a company name, but yfinance can't reliably search by name.

    # --- Limitation Acknowledged ---
    # yfinance does NOT have a robust function to search for tickers by company name.
    # A proper name-to-ticker search with suggestions requires a dedicated financial data API
    # or a pre-compiled, searchable database, which is beyond the scope of this script
    # using only yfinance.
    # Therefore, the primary method here is validating if the input IS a ticker.

    # If no valid ticker was found from the direct attempt
    return None, None

# Provided and completed function to analyze stock
def analyze_stock(ticker, start_date):
    """
    Analyzes a stock using yfinance, calculates moving averages and RSI,
    displays data, and generates charts including revenue, dividends, and free cash flow.
    """
    try:
        # Check if the ticker is empty before downloading
        if not ticker:
             st.warning("Please enter a ticker symbol to analyze.")
             return None, None

        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for ticker **{ticker}** from **{start_date}**. Please check the ticker symbol and date range.")
            return None, None

        # Calculate indicators
        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get company info, financials, and cash flow
        stock_info = yf.Ticker(ticker)
        info = stock_info.info # Get the info dictionary once
        financials = stock_info.financials
        cashflow = stock_info.cashflow
        long_name = info.get('longName', ticker) # Get the long name, default to ticker

        # Helper function to process financial/cashflow data (handles timezones)
        def process_financial_data(data_series, start_date):
             if data_series.empty:
                  return pd.Series()
             try:
                 # Attempt to localize if index is naive
                 if data_series.index.tz is None:
                      data_series.index = pd.to_datetime(data_series.index).tz_localize('UTC')
                 # Convert to UTC if already timezone-aware but not UTC
                 elif data_series.index.tz != pytz.utc:
                       data_series.index = data_series.index.tz_convert('UTC')
             except Exception as e:
                 st.warning(f"Could not process date index for financial data: {e}. Skipping timezone conversion.")
                 # Fallback: keep index as is if conversion fails

             start_date_utc = pd.to_datetime(start_date)
             # Ensure start_date_utc is timezone-aware for comparison if data_series index is aware
             if data_series.index.tz is not None:
                 start_date_utc = start_date_utc.tz_localize(pytz.utc)

             return data_series[data_series.index >= start_date_utc].sort_index()


        # Get revenue data
        revenue_data = pd.Series()
        if 'Total Revenue' in financials.index:
             revenue_data = financials.loc['Total Revenue']
             revenue_data = process_financial_data(revenue_data, start_date)


        # Get dividend data
        dividends = stock_info.dividends
        dividends = process_financial_data(dividends, start_date)


        # Get free cash flow data
        fcf_data = pd.Series()
        if 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
