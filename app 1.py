import pandas as pd
import requests
import streamlit as st
import matplotlib.pyplot as plt

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

        # Rename columns for easier usage
        stock_data = stock_data.rename(columns={
            'close': 'Close'
        })

        # Retain only the Date and Close columns
        stock_data = stock_data[['Close']]

        # Drop missing values
        stock_data.dropna(inplace=True)

        # Ensure numeric data type for Close column
        stock_data = stock_data.astype({"Close": "float"})

        return stock_data
    except Exception as e:
        st.error(f"Error fetching or processing Apple stock data: {e}")
        return pd.DataFrame()

# Main app
def main():
    st.title("Apple Stock Closing Price Viewer (EOD API)")
    st.write("This app fetches Apple (AAPL) stock data using the EOD API and plots the closing price over time.")

    # Fetch stock data
    stock_data = fetch_apple_stock_data()

    # Validate and display data
    if not stock_data.empty:
        st.write("### Data Preview")
        st.dataframe(stock_data)

        # Plot closing price against date
        st.write("### Apple Stock Closing Price Chart")
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(stock_data.index, stock_data['Close'], label='Closing Price', color='blue')
            plt.title("Apple Stock Closing Prices Over Time", fontsize=16)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Closing Price (USD)", fontsize=12)
            plt.legend(loc="upper left")
            plt.grid(visible=True, linestyle='--', alpha=0.5)
            st.pyplot(plt)
        except ValueError as ve:
            st.error(f"Error plotting the closing price chart: {ve}")
    else:
        st.warning("No data available. Please check the API key or date range.")

if __name__ == "__main__":
    main()
