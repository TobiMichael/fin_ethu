import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Change to DEBUG for more detailed logs

#  API Key
FRED_API_KEY = "5f722c7cb457ce85f5d483c2d32497c5"  # Replace with user provided API Key

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
        df = stock.history(start=start_date, end=end_date, interval="1wk")  # Weekly data
        if df.empty:
            error_message = f"No data found for symbol {symbol} within the specified date range."
            st.error(error_message)
            logging.error(error_message)
            return None

        # Calculate moving averages
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        logging.info(f"Successfully fetched and processed stock data for {symbol}")
        return df
    except Exception as e:
        error_message = f"Error fetching stock data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
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
        logging.warning(f"plot_stock_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
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
            template='plotly_dark',
            yaxis_type="log",  # log scale is always used
            height=500,
        )
        logging.info(f"Successfully plotted stock data for {symbol}")
        return fig
    except Exception as e:
        error_message = f"Error plotting stock data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None



def get_economic_data(start_date, end_date):
    """
    Fetches US Federal Funds Rate and GDP data from the Federal Reserve API (FRED).

    Args:
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the Fed Funds Rate and GDP data,
                          or None if an error occurs.
    """
    try:
        logging.info(f"Fetching economic data from {start_date} to {end_date}")
        # Convert dates to string format required by FRED API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # FRED API URLs
        ffr_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DFF&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date_str}&observation_end={end_date_str}"
        gdp_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={FRED_API_KEY}&file_type=json&observation_start={start_date_str}&observation_end={end_date_str}"

        # Fetch data
        try:
            ffr_response = requests.get(ffr_url)
            ffr_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            gdp_response = requests.get(gdp_url)
            gdp_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching data from FRED API: {e}"
            st.error(error_message)
            logging.error(error_message, exc_info=True)
            return None

        # Parse JSON responses
        try:
            ffr_data = json.loads(ffr_response.text)
            gdp_data = json.loads(gdp_response.text)
        except json.JSONDecodeError as e:
            error_message = f"Error decoding JSON response from FRED API: {e}"
            st.error(error_message)
            logging.error(error_message, exc_info=True)
            return None


        # Convert data to pandas DataFrames
        ffr_df = pd.DataFrame(ffr_data['observations'])
        gdp_df = pd.DataFrame(gdp_data['observations'])

        #check if dataframes are empty
        if ffr_df.empty:
            error_message = "Fed Funds Rate data is empty."
            st.error(error_message)
            logging.error(error_message)
            ffr_df = None  # Set to None to indicate an error
        
        if gdp_df.empty:
            error_message = "GDP data is empty."
            st.error(error_message)
            logging.error(error_message)
            gdp_df = None #set to None to indicate an error

        # Convert 'date' to datetime and 'value' to numeric
        if ffr_df is not None: # only convert if not None
            ffr_df['date'] = pd.to_datetime(ffr_df['date'])
            ffr_df['value'] = pd.to_numeric(ffr_df['value'], errors='coerce')  # Handle missing values
            ffr_df = ffr_df.rename(columns={'value': 'Fed Funds Rate'})
        
        if gdp_df is not None: # only convert if not None
            gdp_df['date'] = pd.to_datetime(gdp_df['date'])
            gdp_df['value'] = pd.to_numeric(gdp_df['value'], errors='coerce')  # Handle missing values
            gdp_df = gdp_df.rename(columns={'value': 'GDP'})
        

        # Merge the DataFrames on 'date'
        if ffr_df is not None and gdp_df is not None:
            economic_df = pd.merge(ffr_df, gdp_df, on='date', how='outer') # Use outer join to keep all dates
            economic_df = economic_df.set_index('date')
            logging.info("Successfully fetched and processed economic data.")
            return economic_df
        elif ffr_df is not None:
            logging.info("Successfully fetched Fed Funds Rate data. GDP data was not available.")
            return ffr_df
        elif gdp_df is not None:
            logging.info("Successfully fetched GDP data. Fed Funds Rate data was not available.")
            return gdp_df
        else:
            error_message = "Failed to fetch both Fed Funds Rate and GDP data."
            st.error(error_message)
            logging.error(error_message)
            return None

    except Exception as e:
        error_message = f"An error occurred while fetching economic data: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None



def plot_economic_data(df):
    """
    Plots the US Federal Funds Rate and GDP on the same chart.

    Args:
        df (pandas.DataFrame): The DataFrame containing the economic data.

    Returns:
        plotly.graph_objects.Figure: The plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning("plot_economic_data called with empty DataFrame")
        return None

    try:
        fig = go.Figure()
        
        # Determine which data is available and add traces accordingly
        if 'Fed Funds Rate' in df.columns and 'GDP' in df.columns:
            # Add Fed Funds Rate trace
            fig.add_trace(go.Scatter(x=df.index, y=df['Fed Funds Rate'], name='Fed Funds Rate', line=dict(color='blue')))
            # Add GDP trace
            fig.add_trace(go.Scatter(x=df.index, y=df['GDP'], name='US GDP', line=dict(color='green'), yaxis="y2"))

            # Define layout with two y-axes
            fig.update_layout(
                title='US Federal Funds Rate and GDP',
                xaxis_title='Date',
                yaxis_title='Fed Funds Rate (%)',
                yaxis2=dict(
                    title='US GDP (Billions USD)',
                    overlaying='y',
                    side='right'
                ),
                legend_title='Legend',
                template='plotly_dark',
                height=500,
            )
        elif 'Fed Funds Rate' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Fed Funds Rate'], name='Fed Funds Rate', line=dict(color='blue')))
            fig.update_layout(
                title='US Federal Funds Rate',
                xaxis_title='Date',
                yaxis_title='Fed Funds Rate (%)',
                legend_title='Legend',
                template='plotly_dark',
                height=500,
            )
        elif 'GDP' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['GDP'], name='US GDP', line=dict(color='green')))
            fig.update_layout(
                title='US GDP',
                xaxis_title='Date',
                yaxis_title='US GDP (Billions USD)',
                legend_title='Legend',
                template='plotly_dark',
                height=500,
            )
        else:
            error_message = "No valid data to plot in economic data"
            st.error(error_message)
            logging.error(error_message)
            return None
        
        logging.info("Successfully plotted economic data.")
        return fig
    except Exception as e:
        error_message = f"Error plotting economic data: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None



def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(layout="wide") # Wide mode

    # Sidebar
    st.sidebar.title('Stock and Economic Data App')
    default_stock = "AAPL"  # Set Apple as the default
    stock_symbol = st.sidebar.text_input('Enter Stock Symbol (e.g., AAPL, GOOG, MSFT)', default_stock).upper()

    # Date range selection using buttons in sidebar
    st.sidebar.subheader("Select Date Range")
    today = datetime.today()
    years = [1, 5, 10, 20, 25]
    cols = st.sidebar.columns(len(years))  # create as many columns as there are years
    selected_time_frame = 5  # Default to 5 years
    for i, year in enumerate(years):
        with cols[i]:  # iterate through the columns
            if st.button(f"<span style='font-size: 10px;'>{year} Year{'s' if year > 1 else ''}</span>",
                       key=f"year_button_{year}"):
                selected_time_frame = year
    start_date = today - relativedelta(years=selected_time_frame)
    end_date = today

    # Main page
    st.header(f"Stock Data for {stock_symbol}")
    # Fetch and plot stock data
    stock_df = get_stock_data(stock_symbol, start_date, end_date)
    if stock_df is not None:
        stock_fig = plot_stock_data(stock_df, stock_symbol)
        if stock_fig is not None:
            st.plotly_chart(stock_fig, use_container_width=True)
        else:
            st.warning("No stock plot to display.")  # show a warning message
    else:
        st.info("Please enter a valid stock symbol and date range.")  # Only show if user intends to see the chart
    
    # Fetch and plot economic data in expander
    with st.expander("Economic Data: Federal Funds Rate and GDP"):
        economic_df = get_economic_data(start_date, end_date)
        if economic_df is not None:
            economic_fig = plot_economic_data(economic_df)
            if economic_fig is not None:
                st.plotly_chart(economic_fig, use_container_width=True)
            else:
                st.warning("No economic data plot to display.")
        else:
            st.info("Unable to fetch economic data.") # Only show if user intends to see the chart
        

if __name__ == "__main__":
    main()

