import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf

# Fetch and clean stock data
def fetch_apple_stock_data():
    start_date = "2000-01-01"
    end_date = "2025-03-10"

    try:
        stock_data = yf.download("AAPL", start=start_date, end=end_date)

        # Clean data
        stock_data.dropna(inplace=True)
        stock_data = stock_data.astype({
            "Open": "float",
            "High": "float",
            "Low": "float",
            "Close": "float",
            "Volume": "float"
        })
        stock_data.index.name = 'Date'
        return stock_data
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

# Main app
def main():
    st.title("Apple Stock Price Viewer")
    st.write("Visualizing Apple stock data with cleaned data handling.")

    # Fetch stock data
    stock_data = fetch_apple_stock_data()

    # Display raw data and chart
    if not stock_data.empty:
        st.write("### Raw Stock Data")
        st.dataframe(stock_data)

        st.write("### Apple Stock Candlestick Chart")
        try:
            fig, axes = mpf.plot(
                stock_data,
                type='candle',
                style='charles',
                title="Apple Stock Prices (2000-2025)",
                volume=True,
                ylabel="Stock Price (USD)",
                returnfig=True
            )
            st.pyplot(fig)
        except ValueError as ve:
            st.error(f"Error creating candlestick chart: {ve}")
    else:
        st.warning("No data available. Please check the date range or data source.")

if __name__ == "__main__":
    main()

