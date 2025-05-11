import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json

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
        template='plotly_dark',
        yaxis_type="log",  # log scale is always used
        height=500,
    )
    return fig



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
        # Convert dates to string format required by FRED API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # FRED API URLs
        ffr_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DFF&api_key=5f722c7cb457ce85f5d483c2d32497c5&file_type=json&observation_start={start_date_str}&observation_end={end_date_str}"  # Replace YOUR_API_KEY
        gdp_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=5f722c7cb457ce85f5d483c2d32497c5&file_type=json&observation_start={start_date_str}&observation_end={end_date_str}"  # Replace YOUR_API_KEY

        # Fetch data
        ffr_response = requests.get(ffr_url)
        gdp_response = requests.get(gdp_url)

        # Parse JSON responses
        ffr_data = json.loads(ffr_response.text)
        gdp_data = json.loads(gdp_response.text)

        # Convert data to pandas DataFrames
        ffr_df = pd.DataFrame(ffr_data['observations'])
        gdp_df = pd.DataFrame(gdp_data['observations'])

        # Convert 'date' to datetime and 'value' to numeric
        ffr_df['date'] = pd.to_datetime(ffr_df['date'])
        ffr_df['value'] = pd.to_numeric(ffr_df['value'], errors='coerce')  # Handle missing values
        gdp_df['date'] = pd.to_datetime(gdp_df['date'])
        gdp_df['value'] = pd.to_numeric(gdp_df['value'], errors='coerce')  # Handle missing values
        
        # Rename the 'value' column
        ffr_df = ffr_df.rename(columns={'value': 'Fed Funds Rate'})
        gdp_df = gdp_df.rename(columns={'value': 'GDP'})

        # Merge the DataFrames on 'date'
        economic_df = pd.merge(ffr_df, gdp_df, on='date', how='outer') # Use outer join to keep all dates

        #set date as index
        economic_df = economic_df.set_index('date')
        
        return economic_df

    except Exception as e:
        st.error(f"An error occurred while fetching economic data: {e}")
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
        return None

    fig = go.Figure()
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
    return fig



def main():
    """
    Main function to run the Streamlit application.
    """
    
