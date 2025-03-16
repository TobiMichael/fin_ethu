import pandas as pd
import streamlit as st
from datetime import datetime
import pandas_datareader.data as web

# Fetching Federal Reserve rate data
def fetch_fed_rate_data():
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

# Fetching stock data for Apple using pandas_datareader
def fetch_stock_data():
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2025, 3, 10)

    # Use pandas_datareader to get data from Yahoo Finance
    stock_data = web.DataReader("AAPL", "yahoo", start_date, end_date)
    stock_data.reset_index(inplace=True)  # Reset index for easier handling
    stock_data.rename(columns={"Date": "Stock Date"}, inplace=True)  # Rename date column
    return stock_data

# Streamlit app
def main():
    st.title("Apple Stock vs Federal Reserve Rate")
    st.write("This app displays Apple stock prices compared with the Federal Reserve interest rates over time.")

    # Fetch and process Fed rate data
    fed_data = fetch_fed_rate_data()
    if not fed_data.empty:
        fed_data['Date'] = pd.to_datetime(fed_data['Date'])

    # Fetch and process stock data
    stock_data = fetch_stock_data()

    if not stock_data.empty and not fed_data.empty:
        # Plotting stock prices
        st.write("### Apple Stock Price")
        st.line_chart(stock_data.set_index("Stock Date")["Close"])  # Plot stock closing prices

        # Plotting Fed rates
        st.write("### Federal Reserve Rates")
        st.line_chart(fed_data.set_index("Date")["Rate"])  # Plot Fed rates

        # Combine both datasets for easier analysis
        combined_data = pd.merge_asof(stock_data.sort_values("Stock Date"), 
                                       fed_data.sort_values("Date"), 
                                       left_on="Stock Date", 
                                       right_on="Date")

        # Display the combined data
        st.write("### Combined Data")
        st.dataframe(combined_data)
    else:
        st.warning("No data available to display.")

if __name__ == '__main__':
    main()
