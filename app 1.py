import pandas as pd
import streamlit as st
import mplfinance as mpf
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
    stock_data.index.name = 'Date'  # Ensure proper index name for mplfinance
    return stock_data

# Streamlit app
def main():
    st.title("Apple Stock vs Federal Reserve Rate")
    st.write("This app visualizes Apple stock prices (as a candlestick chart) alongside Federal Reserve interest rates.")

    # Fetch and process Fed rate data
    fed_data = fetch_fed_rate_data()
    if not fed_data.empty:
        fed_data['Date'] = pd.to_datetime(fed_data['Date'])
        fed_data.set_index('Date', inplace=True)

    # Fetch and process stock data
    stock_data = fetch_stock_data()

    if not stock_data.empty and not fed_data.empty:
        # Display mplfinance plot with Apple stock and Fed Rates
        st.write("### Candlestick Chart: Apple Stock with Fed Funds Rate")

        # Create an additional panel for the Fed Rate
        add_plot_fed = mpf.make_addplot(
            fed_data['Rate'], 
            panel=1, 
            color='red', 
            ylabel='Fed Funds Rate (%)'
        )

        # Create the candlestick chart
        fig, axes = mpf.plot(
            stock_data,
            type='candle',  # Candlestick chart
            style='charles',  # Style for the chart
            title='Apple Stock Prices and Federal Funds Rate',
            addplot=add_plot_fed,
            volume=True,  # Include volume in the plot
            panel_ratios=(3, 1),  # Allocate more space to the stock chart
            returnfig=True
        )

        # Use Streamlit to display the mplfinance figure
        st.pyplot(fig)

        # Display data tables for reference
        st.write("### Federal Reserve Rate Data:")
        st.dataframe(fed_data)

        st.write("### Apple Stock Data:")
        st.dataframe(stock_data)
    else:
        st.warning("No data available to display.")

if __name__ == '__main__':
    main()
