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

        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

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
        # Create the candlestick chart
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
            yaxis_type="log",
            height=500,
        )
        logging.info(f"Successfully plotted stock data for {symbol}")
        return fig
    except Exception as e:
        error_message = f"Error plotting stock data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_rsi_data(df, symbol):
    """
    Plots the RSI data.

    Args:
        df (pandas.DataFrame): The DataFrame containing the stock data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The RSI plot, or None if the DataFrame is empty or RSI is missing.
    """
    if df is None or df.empty or 'RSI' not in df:
        logging.warning(f"plot_rsi_data called with empty DataFrame or missing RSI for symbol {symbol}")
        return None

    try:
        # Create the RSI plot
        fig_rsi = go.Figure(data=[go.Scatter(
            x=df.index,
            y=df['RSI'],
            name='RSI',
            line=dict(color='blue')
        )])

        # Define the layout for the RSI plot
        fig_rsi.update_layout(
            title=f'{symbol} Relative Strength Index (RSI)',
            xaxis_title='Date',
            yaxis_title='RSI',
            template='plotly_dark',
            height=300,
            yaxis_range=[0, 100]  # Ensure y-axis range is 0-100 for RSI
        )
        logging.info(f"Successfully plotted RSI data for {symbol}")
        return fig_rsi
    except Exception as e:
        error_message = f"Error plotting RSI data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_returns_data(df, symbol):
    """
    Plots the stock returns.

    Args:
        df (pandas.DataFrame): The DataFrame containing the stock data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The returns plot, or None if the DataFrame is empty or returns cannot be calculated.
    """
    if df is None or df.empty:
        logging.warning(f"plot_returns_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Calculate returns
        df['Returns'] = df['Close'].pct_change() * 100
        df = df.dropna()  # Drop the first row with NaN return

        # Create the returns plot
        fig_returns = go.Figure(data=[go.Scatter(
            x=df.index,
            y=df['Returns'],
            name='Returns',
            line=dict(color='green')
        )])

        # Define the layout for the returns plot
        fig_returns.update_layout(
            title=f'{symbol} Stock Returns (Weekly)',
            xaxis_title='Date',
            yaxis_title='Returns (%)',
            template='plotly_dark',
            height=300,
        )
        logging.info(f"Successfully plotted returns data for {symbol}")
        return fig_returns
    except Exception as e:
        error_message = f"Error plotting returns data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def get_revenue_data(symbol):
    """
    Fetches revenue data from yfinance.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        pandas.DataFrame: A DataFrame containing the revenue data,
                          or None if an error occurs or no revenue data is available.
    """
    try:
        logging.info(f"Fetching revenue data for {symbol}")
        stock = yf.Ticker(symbol)
        # Fetch quarterly revenue
        revenue_data = stock.quarterly_income_stmt
        if revenue_data is None or revenue_data.empty:
            logging.warning(f"No revenue data found for symbol {symbol}")
            return None

        # Convert to DataFrame and transpose
        revenue_df = revenue_data.T
        revenue_df.index = pd.to_datetime(revenue_df.index)
        revenue_df = revenue_df.sort_index()  # Sort by date

        # Select the revenue column
        if 'Total Revenue' in revenue_df.columns:
            revenue_df = revenue_df[['Total Revenue']]
        elif 'Revenue' in revenue_df.columns:
            revenue_df = revenue_df[['Revenue']]
        else:
            logging.warning(f"No Revenue or Total Revenue column found for symbol {symbol}")
            return None
        
        revenue_df = revenue_df.dropna()

        logging.info(f"Successfully fetched revenue data for {symbol}")
        return revenue_df
    except Exception as e:
        error_message = f"Error fetching revenue data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_revenue_data(df, symbol):
    """
    Plots the revenue data.

    Args:
        df (pandas.DataFrame): The DataFrame containing the revenue data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The revenue plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning(f"plot_revenue_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Create the revenue plot
        fig_revenue = go.Figure(data=[go.Bar(
            x=df.index,
            y=df.iloc[:, 0],  # Use the first column for revenue data
            name='Revenue',
            marker_color='purple'
        )])

        # Define the layout for the revenue plot
        fig_revenue.update_layout(
            title=f'{symbol} Quarterly Revenue',
            xaxis_title='Date',
            yaxis_title='Revenue',
            template='plotly_dark',
            height=300,
        )
        logging.info(f"Successfully plotted revenue data for {symbol}")
        return fig_revenue
    except Exception as e:
        error_message = f"Error plotting revenue data for {symbol}: {e}"
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
            if st.button(f"{year} Year{'s' if year > 1 else ''}"):
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

        # Plot returns data
        returns_fig = plot_returns_data(stock_df, stock_symbol)
        if returns_fig is not None:
            st.plotly_chart(returns_fig, use_container_width=True)
        else:
            st.warning("No returns plot to display.")

        # Fetch and plot revenue data
        revenue_df = get_revenue_data(stock_symbol)
        if revenue_df is not None:
            revenue_fig = plot_revenue_data(revenue_df, stock_symbol)
            if revenue_fig is not None:
                st.plotly_chart(revenue_fig, use_container_width=True)
            else:
                st.warning("No revenue plot to display.")
        else:
            st.info("Revenue data is not available for this stock.")

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

    # RSI Explanation
    with st.expander("Relative Strength Index (RSI)"):
        
        # Plot RSI data
        if stock_df is not None:
            rsi_fig = plot_rsi_data(stock_df, stock_symbol)
            if rsi_fig is not None:
                st.plotly_chart(rsi_fig, use_container_width=True)
            else:
                st.warning("No RSI plot to display.")

if __name__ == "__main__":
    main()
