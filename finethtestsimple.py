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

def plot_revenue_data(df, symbo
