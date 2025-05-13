import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date # Import date as well
import logging # Import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    body {
        color: #333;
        background-color: #f0f2f6;
    }
    /* Adjusting stPlot styling for Plotly charts */
    .stPlotlyChart {
         padding: 10px;
         border-radius: 5px;
         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
         margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Keeping calculate_rsi for potential future use, though not used in the new plot function
def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_up = up.rolling(window).mean()
    average_down = down.rolling(window).mean()
    # Handle division by zero for RS calculation
    rs = average_up / average_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Adopted get_stock_data function
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
        logging.info(f"Fetching stock data for {symbol} from {start_date} to {end_date}")
        stock = yf.Ticker(symbol)
        # Fetch weekly data as specified in the provided snippet
        df = stock.history(start=start_date, end=end_date, interval="1wk")
        if df.empty:
            error_message = f"No data found for symbol {symbol} within the specified date range."
            st.warning(error_message) # Use st.warning for user feedback
            logging.warning(error_message) # Use logging.warning for logs
            return None

        # Calculate moving averages as specified in the provided snippet
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()

        logging.info(f"Successfully fetched data for {symbol}")
        return df # Return the DataFrame

    except Exception as e:
        error_message = f"Error fetching data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

# Adopted plot_stock_data function
def plot_stock_data(df, symbol):
    """
    Plots the stock price as a candlestick chart and moving averages using Plotly.

    Args:
        df (pandas.DataFrame): The DataFrame containing the stock data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning(f"plot_stock_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Create the candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=f'{symbol} Price'
        )])
        # Add moving averages
        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name='50-week MA', line=dict(color='orange'))) # Changed to week as interval is 1wk
        fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], name='200-week MA', line=dict(color='red'))) # Changed to week as interval is 1wk

        fig.update_layout(
            title=f'{symbol} Stock Price with Moving Averages (Weekly)',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            legend_title='Legend',
            template='plotly_dark', # Using plotly_dark template
            yaxis_type="log", # Using log scale for y-axis
            height=600, # Adjusted height
            xaxis_rangeslider_visible=False # Hide rangeslider for cleaner look
        )
        logging.info(f"Successfully plotted stock data for {symbol}")
        return fig # Return the figure

    except Exception as e:
        error_message = f"Error plotting stock data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

# Removed the old plot_stock_comparison function as the new approach focuses on individual stock analysis with candlestick charts.
# Removed the old analyze_stock function as its logic is now integrated into main using the new functions.


def main():
    st.title("Finance Enthusiast")

    col1, col2 = st.columns(2)

    with st.sidebar:
        st.header("Stock Analysis")
        ticker1 = st.text_input("Enter first stock ticker:", "AAPL").upper()
        ticker2 = st.text_input("Enter second stock ticker:", "GOOGL").upper()

        # Date inputs for start and end dates
        start_date = st.date_input("Start date:", datetime.now().date() - pd.DateOffset(years=5).date()) # Default to 5 years ago
        end_date = st.date_input("End date:", datetime.now().date()) # Default to today's date

        analyze_button = st.button("Analyze Stocks")

    if analyze_button:
        # Convert date objects to datetime for yfinance compatibility if needed, though yfinance handles date objects
        # start_date_dt = datetime.combine(start_date, datetime.min.time())
        # end_date_dt = datetime.combine(end_date, datetime.max.time()) # Use end of day for end date

        with col1:
            st.subheader(f"Analysis for {ticker1}")
            # Use the new get_stock_data function
            stock_df1 = get_stock_data(ticker1, start_date, end_date)
            if stock_df1 is not None:
                # Display latest data including Open, Close, MA50, MA200
                latest_data1 = stock_df1[['Open', 'Close', 'MA50', 'MA200']].tail(1)
                st.write("Latest Data:")
                st.dataframe(latest_data1)

                # Use the new plot_stock_data function
                stock_fig1 = plot_stock_data(stock_df1, ticker1)
                if stock_fig1 is not None:
                    st.plotly_chart(stock_fig1, use_container_width=True)
                else:
                    st.warning(f"Could not generate plot for {ticker1}.")

        with col2:
            st.subheader(f"Analysis for {ticker2}")
            # Use the new get_stock_data function
            stock_df2 = get_stock_data(ticker2, start_date, end_date)
            if stock_df2 is not None:
                 # Display latest data including Open, Close, MA50, MA200
                latest_data2 = stock_df2[['Open', 'Close', 'MA50', 'MA200']].tail(1)
                st.write("Latest Data:")
                st.dataframe(latest_data2)

                # Use the new plot_stock_data function
                stock_fig2 = plot_stock_data(stock_df2, ticker2)
                if stock_fig2 is not None:
                    st.plotly_chart(stock_fig2, use_container_width=True)
                else:
                    st.warning(f"Could not generate plot for {ticker2}.")

        # The comparison plot section has been removed as the new plotting approach is for individual candlestick charts.


if __name__ == "__main__":
    main()
