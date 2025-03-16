import pandas as pd
import streamlit as st
import mplfinance as mpf
from datetime import datetime
import pandas_datareader.data as web

# Fetching Federal Reserve rate data
def fetch_fed_rate_data():
    # Example dataset - Replace with actual data source or API call
    dates = pd.date_range(start='2000-01-01', end='2025-03-10', freq='AS')
    rates = [6.5, 6.0, 1.75, 1.0, 2.0, 3.25, 0.0, 0.25, 0.5, 2.0, 2.25, 0.25, 
             0.1, 0.25, 0.75, 1.5, 2.5, 2.25, 4.5, 4.75, 5.0, 5.5, 5.0, 5.25, 5.5]

    # Adjust length of rates to match length of dates
    if len(rates) < len(dates):
        rates.extend([None] * (len(dates) - len(rates)))  # Fill with None if rates are too few

    data = {
        'Date': dates,
        'Rate': rates
    }

    return pd.DataFrame(data)

# Fetching stock data for Apple
def fetch_apple_stock_data():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2025, 3, 10)

    # Use pandas_datareader to get data from Yahoo Finance
    stock_data = web.DataReader("AAPL", "yahoo", start_date, end_date)
    stock_data.index.name = 'Date'  # Ensure proper index name for mplfinance
    return stock_data

# Streamlit app
def main():
    st.title("Apple Stock Prices and Federal Reserve Rates")
    st.write("This app visualizes Apple stock prices and Federal Reserve interest rates.")

    # Fetch and process Federal Reserve rate data
    fed_data = fetch_fed_rate_data()
    if not fed_data.empty:
        fed_data['Date'] = pd.to_datetime(fed_data['Date'])
        fed_data.set_index('Date', inplace=True)

    # Fetch and process Apple stock data
    stock_data = fetch_apple_stock_data()

    if not stock_data.empty and not fed_data.empty:
        # Display mplfinance plot with Apple stock
        st.write("### Candlestick Chart: Apple Stock Prices")

        # Create the candlestick chart
        fig, axes = mpf.plot(
            stock_data,
            type='candle',       # Use candlestick chart
            style='charles',     # Use a pre-defined chart style
            title="Apple Stock Prices (2000-2025)",
            volume=True,         # Display volume data
            ylabel="Stock Price (USD)",
            returnfig=True
        )

        # Display the mplfinance chart
        st.pyplot(fig)

        # Display Federal Reserve rate data
        st.write("### Federal Reserve Rates")
        st.line_chart(fed_data["Rate"])  # Plot Fed Rates over time

        # Display data tables for reference
        st.write("### Apple Stock Data:")
        st.dataframe(stock_data)

        st.write("### Federal Reserve Rate Data:")
        st.dataframe(fed_data)
    else:
        st.warning("No data available to display. Please check your data source.")

if __name__ == '__main__':
    main()
