import pandas as pd
import requests
import streamlit as st
import mplfinance as mpf

# Fetch stock data using EOD API
def fetch_apple_stock_data():
    api_key = "DEMO"  # Replace with your EOD API key
    symbol = "AAPL.US"  # Apple stock in EOD API format
    start_date = "2000-01-01"
    end_date = "2025-03-10"

    # EOD API endpoint
    url = f"https://eodhd.com/api/eod/{symbol}?api_token={api_key}&from={start_date}&to={end_date}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses (4xx or 5xx)

        # Parse JSON response
        data = response.json()
        stock_data = pd.DataFrame(data)

        # Process and clean the DataFrame
        stock_data['Date'] = pd.to_datetime(stock_data['date'])
        stock_data.set_index('Date', inplace=True)

        # Rename columns for mplfinance compatibility
        stock_data = stock_data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        stock_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]  # Keep required columns

        # Clean data
        stock_data.dropna(inplace=True)
        stock_data = stock_data.astype({
            "Open": "float",
            "High": "float",
            "Low": "float",
            "Close": "float",
            "Volume": "float"
        })

        return stock_data
    except Exception as e:
        st.error(f"Error fetching or processing Apple stock data: {e}")
        return pd.DataFrame()

# Main app
def main():
    st.title("Apple Stock Price Viewer (EOD API)")
    st.write("This app fetches Apple (AAPL) stock data using the EOD API and visualizes it.")

    # Fetch stock data
    stock_data = fetch_apple_stock_data()

    # Validate and display data
    if not stock_data.empty:
        st.write("### Data Preview")
        st.dataframe(stock_data)

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
        st.warning("No data available. Please check the API key or date range.")

if __name__ == "__main__":
    main()
