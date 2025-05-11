import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_stock_data(symbol, start_date, end_date):
    """
    Fetches stock data from yfinance and calculates moving averages.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the stock data,
                          or None if an error occurs.
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date, interval="1wk")  # Weekly data
        if df.empty:
            st.error(f"No data found for symbol {symbol} within the specified date range.")
            return None

        # Calculate moving averages
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        return df
    except Exception as e:
        st.error(f"An error occurred while fetching data for {symbol}: {e}")
        return None

def plot_stock_data(df, symbol):
    """
    Plots the stock price as a candlestick chart and moving averages.

    Args:
        df (pandas.DataFrame): The DataFrame containing the stock data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        return None

    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=f'{symbol} Price'
    )])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name='50-day MA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name='200-day MA', line=dict(color='red')))

    fig.update_layout(
        title=f'{symbol} Stock Price with Moving Averages (Weekly)',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        legend_title='Legend',
        template='plotly_dark'  # Use a dark theme
    )
    return fig

def main():
    """
    Main function to run the Streamlit application.
    """
    st.title('Stock Data App')

    # Stock input with default value
    default_stock = "AAPL"  # Set Apple as the default
    stock_symbol = st.text_input('Enter Stock Symbol (e.g., AAPL, GOOG, MSFT)', default_stock).upper()

    # Date range selection
    today = datetime.today()
    years = [1, 5, 10, 20, 25]
    time_frame = st.selectbox("Select Time Frame", years, index=1) # Default to 5 years
    start_date = today - relativedelta(years=time_frame)
    end_date = today

    # Fetch and plot data
    df = get_stock_data(stock_symbol, start_date, end_date)
    if df is not None:
        fig = plot_stock_data(df, stock_symbol)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No plot to display.") # show a warning message
    else:
        st.info("Please enter a valid stock symbol and date range.") # show an info message

if __name__ == "__main__":
    main()
