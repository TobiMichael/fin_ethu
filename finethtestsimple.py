import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
import logging
import pytz  # Import pytz

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



def get_revenue_data(symbol, start_date, end_date):
    """
    Fetches revenue data from yfinance, filtered by date range.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the revenue data,
                          or None if an error occurs or no revenue data is available.
    """
    try:
        logging.info(f"Fetching revenue data for {symbol} from {start_date} to {end_date}")
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
        
        # Filter by date range
        revenue_df = revenue_df[(revenue_df.index >= start_date) & (revenue_df.index <= end_date)]
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

def get_dividend_data(symbol, start_date, end_date):
    """
    Fetches dividend data from yfinance.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the dividend data,
                          or None if an error occurs.
    """
    try:
        logging.info(f"Fetching dividend data for {symbol} from {start_date} to {end_date}")
        stock = yf.Ticker(symbol)
        dividends = stock.dividends
        if dividends.empty:
            logging.warning(f"No dividend data found for symbol {symbol}")
            return None

        # Convert to DataFrame
        dividends_df = pd.DataFrame(dividends)
        dividends_df.index = pd.to_datetime(dividends_df.index)

        # Filter by date range, handling timezones
        start_date_tz = start_date.replace(tzinfo=pytz.utc)  # Ensure start_date is UTC
        end_date_tz = end_date.replace(tzinfo=pytz.utc)      # Ensure end_date is UTC

        dividends_df = dividends_df[(dividends_df.index >= start_date_tz) & (dividends_df.index <= end_date_tz)]
        dividends_df = dividends_df.sort_index()

        logging.info(f"Successfully fetched dividend data for {symbol}")
        return dividends_df
    except Exception as e:
        error_message = f"Error fetching dividend data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_dividend_data(df, symbol):
    """
    Plots the dividend data.

    Args:
        df (pandas.DataFrame): The DataFrame containing the dividend data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The dividend plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning(f"plot_dividend_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Create the dividend plot
        fig_dividend = go.Figure(data=[go.Bar(
            x=df.index,
            y=df['Dividends'],
            name='Dividends',
            marker_color='green'
        )])

        # Define the layout for the dividend plot
        fig_dividend.update_layout(
            title=f'{symbol} Dividends',
            xaxis_title='Date',
            yaxis_title='Dividends (USD)',
            template='plotly_dark',
            height=300,
        )
        logging.info(f"Successfully plotted dividend data for {symbol}")
        return fig_dividend
    except Exception as e:
        error_message = f"Error plotting dividend data for {symbol}: {e}"
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
        ffr_df = pd.DataFrame
