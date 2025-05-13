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

# World Bank API base URL
WORLD_BANK_API_URL = "http://api.worldbank.org/v2/country/all/indicator/"

# World Bank Series IDs
GDP_SERIES_ID = "NY.GDP.MKTP.CD" # GDP (current US$)
INFLATION_SERIES_ID = "FP.CPI.TOTL.ZG" # Inflation, consumer prices (annual %)


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
        error_message = f"Error plotting dividend data for {symbol}: {e}"
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


def get_quarterly_free_cash_flow_data(symbol, start_date, end_date):
    """
    Fetches quarterly free cash flow data from yfinance, filtered by date range.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the free cash flow data,
                          or None if an error occurs or no free cash flow data is available.
    """
    try:
        logging.info(f"Fetching quarterly free cash flow data for {symbol} from {start_date} to {end_date}")
        stock = yf.Ticker(symbol)
        # Fetch quarterly cash flow
        cashflow_data = stock.quarterly_cashflow
        if cashflow_data is None or cashflow_data.empty:
            logging.warning(f"No quarterly cash flow data found for symbol {symbol}")
            return None

        # Convert to DataFrame and transpose
        cashflow_df = cashflow_data.T
        cashflow_df.index = pd.to_datetime(cashflow_df.index)
        cashflow_df = cashflow_df.sort_index()  # Sort by date

        # Select the 'Free Cash Flow' column (it's a column in this structure)
        if 'Free Cash Flow' in cashflow_df.columns:
            free_cash_flow_df = cashflow_df[['Free Cash Flow']]
        else:
            logging.warning(f"No 'Free Cash Flow' column found for symbol {symbol} in quarterly cash flow data.")
            return None
        
        # Filter by date range
        free_cash_flow_df = free_cash_flow_df[(free_cash_flow_df.index >= start_date) & (free_cash_flow_df.index <= end_date)]
        free_cash_flow_df = free_cash_flow_df.dropna()


        logging.info(f"Successfully fetched quarterly free cash flow data for {symbol}")
        return free_cash_flow_df
    except Exception as e:
        error_message = f"Error fetching quarterly free cash flow data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_quarterly_free_cash_flow_data(df, symbol):
    """
    Plots the quarterly free cash flow data.

    Args:
        df (pandas.DataFrame): The DataFrame containing the free cash flow data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The free cash flow plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning(f"plot_quarterly_free_cash_flow_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Create the free cash flow plot
        fig_free_cash_flow = go.Figure(data=[go.Bar(
            x=df.index,
            y=df['Free Cash Flow'],  # Use the 'Free Cash Flow' column
            name='Free Cash Flow',
            marker_color='teal'
        )])

        # Define the layout for the free cash flow plot
        fig_free_cash_flow.update_layout(
            title=f'{symbol} Quarterly Free Cash Flow',
            xaxis_title='Date',
            yaxis_title='Free Cash Flow (USD)',
            template='plotly_dark',
            height=300,
        )
        logging.info(f"Successfully plotted quarterly free cash flow data for {symbol}")
        return fig_free_cash_flow
    except Exception as e:
        error_message = f"Error plotting quarterly free cash flow data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def get_annual_free_cash_flow_data(symbol):
    """
    Fetches annual free cash flow data from yfinance.

    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').

    Returns:
        pandas.DataFrame: A DataFrame containing the annual free cash flow data,
                          or None if an error occurs or no free cash flow data is available.
    """
    try:
        logging.info(f"Fetching annual free cash flow data for {symbol}")
        stock = yf.Ticker(symbol)
        # Fetch annual cash flow
        cashflow_data = stock.cashflow
        if cashflow_data is None or cashflow_data.empty:
            logging.warning(f"No annual cash flow data found for symbol {symbol}")
            return None

        # Convert to DataFrame and transpose
        cashflow_df = cashflow_data.T
        cashflow_df.index = pd.to_datetime(cashflow_df.index)
        cashflow_df = cashflow_df.sort_index()  # Sort by date

        # Select the 'Free Cash Flow' column
        if 'Free Cash Flow' in cashflow_df.columns:
            free_cash_flow_df = cashflow_df[['Free Cash Flow']]
        else:
            logging.warning(f"No 'Free Cash Flow' column found for symbol {symbol} in annual cash flow data.")
            return None

        free_cash_flow_df = free_cash_flow_df.dropna()

        logging.info(f"Successfully fetched annual free cash flow data for {symbol}")
        return free_cash_flow_df
    except Exception as e:
        error_message = f"Error fetching annual free cash flow data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None

def plot_annual_free_cash_flow_data(df, symbol):
    """
    Plots the annual free cash flow data.

    Args:
        df (pandas.DataFrame): The DataFrame containing the annual free cash flow data.
        symbol (str): The stock symbol.

    Returns:
        plotly.graph_objects.Figure: The free cash flow plot, or None if the DataFrame is empty.
    """
    if df is None or df.empty:
        logging.warning(f"plot_annual_free_cash_flow_data called with empty DataFrame for symbol {symbol}")
        return None

    try:
        # Create the free cash flow plot
        fig_free_cash_flow = go.Figure(data=[go.Bar(
            x=df.index,
            y=df['Free Cash Flow'],  # Use the 'Free Cash Flow' column
            name='Free Cash Flow',
            marker_color='orange' # Using a different color for annual
        )])

        # Define the layout for the free cash flow plot
        fig_free_cash_flow.update_layout(
            title=f'{symbol} Annual Free Cash Flow',
            xaxis_title='Date',
            yaxis_title='Free Cash Flow (USD)',
            template='plotly_dark',
            height=300,
        )
        logging.info(f"Successfully plotted annual free cash flow data for {symbol}")
        return fig_free_cash_flow
    except Exception as e:
        error_message = f"Error plotting annual free cash flow data for {symbol}: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None


def get_economic_data(start_date, end_date):
    """
    Fetches US GDP and Inflation data from the World Bank API.

    Args:
        start_date (datetime): The start date for the data.
        end_date (datetime): The end date for the data.

    Returns:
        pandas.DataFrame: A DataFrame containing the GDP and Inflation data,
                          or None if an error occurs or no data is available.
    """
    try:
        logging.info(f"Fetching economic data from World Bank for {start_date.year} to {end_date.year}")
        
        # World Bank API uses annual data, so use the year range
        date_range = f"{start_date.year}:{end_date.year}"

        # Construct API URLs for GDP and Inflation
        gdp_url = f"{WORLD_BANK_API_URL}{GDP_SERIES_ID}?date={date_range}&format=json&per_page=1000"
        inflation_url = f"{WORLD_BANK_API_URL}{INFLATION_SERIES_ID}?date={date_range}&format=json&per_page=1000"

        # Fetch data
        try:
            gdp_response = requests.get(gdp_url)
            gdp_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            inflation_response = requests.get(inflation_url)
            inflation_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching data from World Bank API: {e}"
            st.error(error_message)
            logging.error(error_message, exc_info=True)
            return None

        # Parse JSON responses
        try:
            gdp_data = json.loads(gdp_response.text)
            inflation_data = json.loads(inflation_response.text)
        except json.JSONDecodeError as e:
            error_message = f"Error decoding JSON response from World Bank API: {e}"
            st.error(error_message)
            logging.error(error_message, exc_info=True)
            return None

        # World Bank API returns a list of lists, the second list contains the data
        gdp_observations = gdp_data[1] if len(gdp_data) > 1 else []
        inflation_observations = inflation_data[1] if len(inflation_data) > 1 else []

        if not gdp_observations and not inflation_observations:
             error_message = "No economic data found from World Bank for the specified date range."
             st.warning(error_message)
             logging.warning(error_message)
             return None

        # Convert data to pandas DataFrames
        gdp_df = pd.DataFrame(gdp_observations)
        inflation_df = pd.DataFrame(inflation_observations)

        economic_df = None

        # Process GDP data if available
        if not gdp_df.empty:
            gdp_df = gdp_df[['date', 'value']].copy() # Select relevant columns
            gdp_df['date'] = pd.to_datetime(gdp_df['date'])
            gdp_df['value'] = pd.to_numeric(gdp_df['value'], errors='coerce')
            gdp_df = gdp_df.rename(columns={'value': 'GDP'})
            gdp_df = gdp_df.dropna()
            economic_df = gdp_df.set_index('date')


        # Process Inflation data if available
        if not inflation_df.empty:
            inflation_df = inflation_df[['date', 'value']].copy() # Select relevant columns
            inflation_df['date'] = pd.to_datetime(inflation_df['date'])
            inflation_df['value'] = pd.to_numeric(inflation_df['value'], errors='coerce')
            inflation_df = inflation_df.rename(columns={'value': 'Inflation'})
            inflation_df = inflation_df.dropna()

            if economic_df is None:
                 economic_df = inflation_df.set_index('date')
            else:
                # Merge with GDP data
                economic_df = pd.merge(economic_df, inflation_df.set_index('date'), left_index=True, right_index=True, how='outer')


        if economic_df is not None and not economic_df.empty:
            economic_df = economic_df.sort_index()
            logging.info("Successfully fetched and processed economic data from World Bank.")
            return economic_df
        else:
            error_message = "Failed to process economic data from World Bank."
            st.error(error_message)
            logging.error(error_message)
            return None


    except Exception as e:  # Catch any exception
        error_message = f"Error occurred while fetching economic data from World Bank: {e}"
        st.error(error_message)
        logging.error(error_message, exc_info=True)
        return None



def plot_economic_data(df):
    """
    Plots the US GDP (Bar) and Inflation (Line) data.

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
        if 'GDP' in df.columns and 'Inflation' in df.columns:
            # Add GDP trace as a Bar chart
            fig.add_trace(go.Bar(x=df.index, y=df['GDP'], name='US GDP (Current USD)', marker_color='green'))
            # Add Inflation trace as a Scatter (Line) chart
            fig.add_trace(go.Scatter(x=df.index, y=df['Inflation'], name='US Inflation (Annual %)', line=dict(color='blue'), yaxis="y2"))

            # Define layout with two y-axes
            fig.update_layout(
                title='US GDP (Annual) and Inflation (Annual)',
                xaxis_title='Date',
                yaxis_title='US GDP (Current USD)',
                yaxis2=dict(
                    title='US Inflation (Annual %)',
                    overlaying='y',
                    side='right'
                ),
                legend_title='Legend',
                template='plotly_dark',
                height=500,
            )
        elif 'GDP' in df.columns:
            # Add GDP trace as a Bar chart
            fig.add_trace(go.Bar(x=df.index, y=df['GDP'], name='US GDP (Current USD)', marker_color='green'))
            fig.update_layout(
                title='US GDP (Annual)',
                xaxis_title='Date',
                yaxis_title='US GDP (Current USD)',
                legend_title='Legend',
                template='plotly_dark',
                height=500,
            )
        elif 'Inflation' in df.columns:
            # Add Inflation trace as a Scatter (Line) chart
            fig.add_trace(go.Scatter(x=df.index, y=df['Inflation'], name='US Inflation (Annual %)', line=dict(color='blue')))
            fig.update_layout(
                title='US Inflation (Annual)',
                xaxis_title='Date',
                yaxis_title='US Inflation (Annual %)',
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
    st.sidebar.title('Enthusiast Space for Finance') # Updated title here
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
    st.title('Enthusiast Space for Finance') # Main title
    # Add the description here
    st.write("Enthusiast Space for Finance helps you look at different companies' stocks and the overall economy. You tell it which company you're interested in and how far back you want to look, it gets the stock data and important economic numbers. Then, it shows all of this to you in easy-to-understand charts.")

    st.header(f"Stock Data for {stock_symbol}")
    # Fetch and plot stock data
    stock_df = get_stock_data(stock_symbol, start_date, end_date)
    if stock_df is not None:
        stock_fig = plot_stock_data(stock_df, stock_symbol)
        if stock_fig is not None:
            st.plotly_chart(stock_fig, use_container_width=True)
        else:
            st.warning("No stock plot to display.")  # show a warning message

   
    # RSI Explanation
    with st.expander("Relative Strength Index (RSI)"):
        
        # Plot RSI data
        if stock_df is not None:
            rsi_fig = plot_rsi_data(stock_df, stock_symbol)
            if rsi_fig is not None:
                st.plotly_chart(rsi_fig, use_container_width=True)
            else:
                st.warning("No RSI plot to display.")
    
    # Fetch and plot dividend data in expander
    with st.expander("Dividends"):
        dividend_df = get_dividend_data(stock_symbol, start_date, end_date)
        if dividend_df is not None:
            dividend_fig = plot_dividend_data(dividend_df, stock_symbol)
            if dividend_fig is not None:
                st.plotly_chart(dividend_fig, use_container_width=True)
            else:
                st.warning("No dividend plot to display.")
        else:
            st.info("Dividend data is not available for this stock within the selected date range.")

    # Fetch and plot revenue data in expander
    with st.expander("Quarterly Revenue"):
        revenue_start_date = datetime(2000, 1, 1)
        revenue_df = get_revenue_data(stock_symbol, revenue_start_date, end_date)
        if revenue_df is not None:
            revenue_fig = plot_revenue_data(revenue_df, stock_symbol)
            if revenue_fig is not None:
                st.plotly_chart(revenue_fig, use_container_width=True)
            else:
                st.warning("No revenue plot to display.")
        else:
            st.info("Revenue data is not available for this stock within the selected date range.")
    
    # Add new expander for Annual Free Cash Flow
    with st.expander("Annual Free Cash Flow"):
        st.markdown("Annual Free Cash Flow represents the cash a company has left over after covering its operating expenses and capital expenditures over a year.")
        annual_free_cash_flow_df = get_annual_free_cash_flow_data(stock_symbol)
        if annual_free_cash_flow_df is not None:
            annual_free_cash_flow_fig = plot_annual_free_cash_flow_data(annual_free_cash_flow_df, stock_symbol)
            if annual_free_cash_flow_fig is not None:
                st.plotly_chart(annual_free_cash_flow_fig, use_container_width=True)
            else:
                st.warning("No annual free cash flow plot to display.")
        else:
            st.info("Annual free cash flow data is not available for this stock.")

    # Keep existing expander for Quarterly Free Cash Flow
    with st.expander("Quarterly Free Cash Flow"):
        quarterly_free_cash_flow_start_date = datetime(2000, 1, 1)
        quarterly_free_cash_flow_df = get_quarterly_free_cash_flow_data(stock_symbol, quarterly_free_cash_flow_start_date, end_date)
        if quarterly_free_cash_flow_df is not None:
            quarterly_free_cash_flow_fig = plot_quarterly_free_cash_flow_data(quarterly_free_cash_flow_df, stock_symbol)
            if quarterly_free_cash_flow_fig is not None:
                st.plotly_chart(quarterly_free_cash_flow_fig, use_container_width=True)
            else:
                st.warning("No quarterly free cash flow plot to display.")
        else:
            st.info("Quarterly free cash flow data is not available for this stock within the selected date range.")


    # Fetch and plot economic data in expander
    with st.expander("Economic Data: GDP and Inflation"): # Updated expander title
        economic_df = get_economic_data(start_date, end_date)
        if economic_df is not None:
            economic_fig = plot_economic_data(economic_df)
            if economic_fig is not None:
                st.plotly_chart(economic_fig, use_container_width=True)
            else:
                st.warning("No economic data plot to display.")
        else:
            st.info("Unable to fetch economic data from World Bank.") # Updated info message



if __name__ == "__main__":
    main()

