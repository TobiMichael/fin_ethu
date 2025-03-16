import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf

# Fetch Apple stock data
def fetch_apple_stock_data():
    start_date = "2000-01-01"
    end_date = "2025-03-10"

    try:
        stock_data = yf.download("AAPL", start=start_date, end=end_date)

        # Remove rows with missing values
        stock_data.dropna(inplace=True)

        # Ensure numeric data
        stock_data = stock_data.astype({
            "Open": "float",
            "High": "float",
            "Low": "float",
            "Close": "float",
            "Volume": "float"
        })
        stock_data.index.name = 'Date'  # Ensure proper index name
        return stock_data
    except Exception as e:
        st.error(f"Error fetching or processing Apple stock data: {e}")
        return pd.DataFrame()

# Main app
def main():
    st.title("Apple Stock Price Viewer")
    st.write("This app fetches and visualizes Apple (AAPL) stock data using cleaned data.")

    # Fetch stock data
    stock_data = fetch_apple_stock_data()

    # Validate and display data
    if not stock_data.empty:
        st.write("### Data Preview")
        st.dataframe(stock_data)

        # Check if required columns are present
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in stock_data.columns]
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            return

        # Plot candlestick chart
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
            st.error(f"Error plotting the candlestick chart: {ve}")
    else:
        st.warning("No data available. Please check the date range or data source.")

if __name__ == "__main__":
    main()
