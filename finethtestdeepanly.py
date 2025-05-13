import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(layout="wide")

# --- Data Fetching and Calculation Functions ---

@st.cache_data # Cache the stock data to avoid re-downloading on every interaction
def get_stock_data(ticker, start_date):
    """
    Downloads stock data from yfinance and calculates moving averages and RSI.
    Data is cached for efficiency.
    """
    try:
        logging.info(f"Fetching data for {ticker} from {start_date}")
        stock_data = yf.download(ticker, start=start_date)
        if stock_data.empty:
            st.warning(f"No data found for {ticker} from {start_date}")
            logging.warning(f"No data found for {ticker} from {start_date}")
            return None

        # Calculate moving averages
        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()

        # Calculate RSI
        delta = stock_data['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        average_up = up.rolling(window=14).mean()
        average_down = down.rolling(window=14).mean()
        rs = average_up / average_down
        stock_data['RSI'] = 100 - (100 / (1 + rs))

        logging.info(f"Successfully fetched and processed data for {ticker}")
        return stock_data
    except Exception as e:
        st.error(f"Error downloading data for {ticker}: {e}")
        logging.error(f"Error downloading data for {ticker}: {e}", exc_info=True)
        return None

@st.cache_data # Cache financial data
def get_financial_data(ticker):
    """Fetches financial data (financials, cashflow) from yfinance."""
    try:
        logging.info(f"Fetching financial data for {ticker}")
        stock_info = yf.Ticker(ticker)
        financials = stock_info.financials
        cashflow = stock_info.cashflow
        info = stock_info.info # Get general info for longName

        logging.info(f"Successfully fetched financial data for {ticker}")
        return financials, cashflow, info
    except Exception as e:
        st.error(f"Error fetching financial data for {ticker}: {e}")
        logging.error(f"Error fetching financial data for {ticker}: {e}", exc_info=True)
        return None, None, None

# --- Plotting Functions ---

def plot_price_and_ma(data, ticker):
    """Plots candlestick chart with moving averages using Plotly."""
    if data is None or data.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Price'))
    fig.add_trace(go.Scatter(x=data.index, y=data['50_MA'], mode='lines', name='50-Day MA'))
    fig.add_trace(go.Scatter(x=data.index, y=data['200_MA'], mode='lines', name='200-Day MA'))

    fig.update_layout(title=f'{ticker} Price (Candlestick) and Moving Averages',
                      xaxis_title='Date', yaxis_title='Price', hovermode='x unified',
                      xaxis_rangeslider_visible=False) # Hide rangeslider for cleaner look
    return fig

def plot_rsi(data, ticker):
    """Plots RSI chart using Plotly."""
    if data is None or data.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
    fig.add_shape(type="line", x0=data.index.min(), x1=data.index.max(), y0=70, y1=70, line=dict(color="red", width=2, dash="dash"))
    fig.add_shape(type="line", x0=data.index.min(), x1=data.index.max(), y0=30, y1=30, line=dict(color="green", width=2, dash="dash"))
    fig.add_annotation(x=data.index.max(), y=70, text="Overbought (70)", showarrow=False, yshift=10)
    fig.add_annotation(x=data.index.max(), y=30, text="Oversold (30)", showarrow=False, yshift=-10)

    fig.update_layout(title=f'{ticker} RSI', xaxis_title='Date', yaxis_title='RSI', hovermode='x unified')
    return fig

def plot_revenue(financials, ticker, start_date):
    """Plots Revenue bar chart using Plotly."""
    revenue_data = pd.Series()
    if financials is not None and 'Total Revenue' in financials.index:
        revenue_data = financials.loc['Total Revenue']
        if not revenue_data.empty:
             if revenue_data.index.tz is None:
                 revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC')
             else:
                 revenue_data.index = revenue_data.index.tz_convert('UTC')
             start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
             revenue_data = revenue_data[revenue_data.index >= start_date_utc]

    fig = go.Figure()
    if not revenue_data.empty:
         fig.add_trace(go.Bar(x=revenue_data.index, y=revenue_data.values, name='Revenue', marker_color='green'))
         fig.update_layout(title=f'{ticker} Revenue', xaxis_title='Date', yaxis_title='Revenue')
    else:
         fig.add_annotation(text="Revenue Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
         fig.update_layout(title=f'{ticker} Revenue (Data Not Available)')
    return fig

def plot_dividends(dividends, ticker, start_date):
    """Plots Dividends bar chart using Plotly."""
    dividends_data = pd.Series()
    if dividends is not None:
        dividends_data = dividends
        if not dividends_data.empty:
             if dividends_data.index.tz is None:
                 dividends_data.index = pd.to_datetime(dividends_data.index).tz_localize('UTC')
             else:
                 dividends_data.index = dividends_data.index.tz_convert('UTC')
             start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
             dividends_data = dividends_data[dividends_data.index >= start_date_utc]

    fig = go.Figure()
    if not dividends_data.empty:
         fig.add_trace(go.Bar(x=dividends_data.index, y=dividends_data.values, name='Dividends', marker_color='orange'))
         fig.update_layout(title=f'{ticker} Dividends', xaxis_title='Date', yaxis_title='Dividend Amount')
    else:
         fig.add_annotation(text="Dividend Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
         fig.update_layout(title=f'{ticker} Dividends (Data Not Available)')
    return fig

def plot_free_cash_flow(cashflow, ticker, start_date):
    """Plots Free Cash Flow bar chart using Plotly."""
    fcf_data = pd.Series()
    if cashflow is not None and 'Free Cash Flow' in cashflow.index:
        fcf_data = cashflow.loc['Free Cash Flow']
        if not fcf_data.empty:
             if fcf_data.index.tz is None:
                 fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
             else:
                 fcf_data.index = fcf_data.index.tz_convert('UTC')
             start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
             fcf_data = fcf_data[fcf_data.index >= start_date_utc]

    fig = go.Figure()
    if not fcf_data.empty:
         fig.add_trace(go.Bar(x=fcf_data.index, y=fcf_data.values, name='Free Cash Flow', marker_color='blue'))
         fig.update_layout(title=f'{ticker} Free Cash Flow', xaxis_title='Date', yaxis_title='Free Cash Flow')
    else:
         fig.add_annotation(text="Free Cash Flow Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
         fig.update_layout(title=f'{ticker} Free Cash Flow (Data Not Available)')
    return fig

def plot_stock_comparison(data1, ticker1, data2, ticker2):
    """Plots the candlestick prices of two stocks for comparison using Plotly."""
    if data1 is None or data2 is None:
        st.warning("Could not plot comparison due to missing data.")
        return None

    fig = go.Figure()

    # Add candlestick trace for ticker 1
    fig.add_trace(go.Candlestick(x=data1.index,
                                 open=data1['Open'],
                                 high=data1['High'],
                                 low=data1['Low'],
                                 close=data1['Close'],
                                 name=f'{ticker1} Price'))

    # Add candlestick trace for ticker 2
    fig.add_trace(go.Candlestick(x=data2.index,
                                 open=data2['Open'],
                                 high=data2['High'],
                                 low=data2['Low'],
                                 close=data2['Close'],
                                 name=f'{ticker2} Price'))


    fig.update_layout(
        title=f'Comparison of {ticker1} and {ticker2} Candlestick Prices', # Updated title
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x unified' # Show tooltip for all traces at the same x-coordinate
    )

    return fig


# --- Main Application Logic ---

def main():
    st.title("Finance Enthusiast")

    col1, col2 = st.columns(2)

    with st.sidebar:
        st.header("Stock Analysis")
        ticker1 = st.text_input("Enter first stock ticker:", "AAPL").upper()
        ticker2 = st.text_input("Enter second stock ticker:", "GOOGL").upper()
        start_year = st.number_input("Enter start year:", min_value=1900, max_value=datetime.now().year, step=1, value=datetime.now().year - 5)
        analyze_button = st.button("Analyze Stocks")

    if analyze_button:
        start_date_str = f"{start_year}-01-01"

        # Fetch data for both tickers once
        data1 = get_stock_data(ticker1, start_date_str)
        financials1, cashflow1, info1 = get_financial_data(ticker1)

        data2 = get_stock_data(ticker2, start_date_str)
        financials2, cashflow2, info2 = get_financial_data(ticker2)


        with col1:
            st.subheader(f"Analysis for {ticker1}")
            if data1 is not None:
                 # Display latest data
                latest_data1 = data1[['Open', 'High', 'Low', 'Close', '50_MA', '200_MA', 'RSI']].tail(1)
                st.write("Latest Data:")
                st.dataframe(latest_data1)

                # Plot and display individual charts in expanders
                with st.expander(f"### {ticker1} - Price (Candlestick) and Moving Averages"):
                    fig_price_ma1 = plot_price_and_ma(data1, ticker1)
                    if fig_price_ma1:
                        st.plotly_chart(fig_price_ma1, use_container_width=True)
                    else:
                        st.write("Price and Moving Averages Chart Not Available")

                with st.expander(f"### {ticker1} - Relative Strength Index (RSI)"):
                    fig_rsi1 = plot_rsi(data1, ticker1)
                    if fig_rsi1:
                        st.plotly_chart(fig_rsi1, use_container_width=True)
                    else:
                         st.write("RSI Chart Not Available")

                with st.expander(f"### {ticker1} - Revenue"):
                    fig_revenue1 = plot_revenue(financials1, ticker1, start_date_str)
                    st.plotly_chart(fig_revenue1, use_container_width=True) # plot_revenue handles "Data Not Available" internally

                with st.expander(f"### {ticker1} - Dividends"):
                    fig_dividends1 = plot_dividends(financials1, ticker1, start_date_str) # Dividends are in financials, not cashflow
                    st.plotly_chart(fig_dividends1, use_container_width=True) # plot_dividends handles "Data Not Available" internally

                with st.expander(f"### {ticker1} - Free Cash Flow"):
                    fig_fcf1 = plot_free_cash_flow(cashflow1, ticker1, start_date_str)
                    st.plotly_chart(fig_fcf1, use_container_width=True) # plot_free_cash_flow handles "Data Not Available" internally


        with col2:
            st.subheader(f"Analysis for {ticker2}")
            if data2 is not None:
                 # Display latest data
                latest_data2 = data2[['Open', 'High', 'Low', 'Close', '50_MA', '200_MA', 'RSI']].tail(1)
                st.write("Latest Data:")
                st.dataframe(latest_data2)

                # Plot and display individual charts in expanders
                with st.expander(f"### {ticker2} - Price (Candlestick) and Moving Averages"):
                    fig_price_ma2 = plot_price_and_ma(data2, ticker2)
                    if fig_price_ma2:
                        st.plotly_chart(fig_price_ma2, use_container_width=True)
                    else:
                         st.write("Price and Moving Averages Chart Not Available")

                with st.expander(f"### {ticker2} - Relative Strength Index (RSI)"):
                    fig_rsi2 = plot_rsi(data2, ticker2)
                    if fig_rsi2:
                        st.plotly_chart(fig_rsi2, use_container_width=True)
                    else:
                         st.write("RSI Chart Not Available")

                with st.expander(f"### {ticker2} - Revenue"):
                    fig_revenue2 = plot_revenue(financials2, ticker2, start_date_str)
                    st.plotly_chart(fig_revenue2, use_container_width=True) # plot_revenue handles "Data Not Available" internally

                with st.expander(f"### {ticker2} - Dividends"):
                    fig_dividends2 = plot_dividends(financials2, ticker2, start_date_str) # Dividends are in financials, not cashflow
                    st.plotly_chart(fig_dividends2, use_container_width=True) # plot_dividends handles "Data Not Available" internally

                with st.expander(f"### {ticker2} - Free Cash Flow"):
                    fig_fcf2 = plot_free_cash_flow(cashflow2, ticker2, start_date_str)
                    st.plotly_chart(fig_fcf2, use_container_width=True) # plot_free_cash_flow handles "Data Not Available" internally


        # Display comparison chart below the columns
        if data1 is not None and data2 is not None:
            with st.expander("### Stock Price Comparison"):
                st.subheader("Comparison of Candlestick Prices")
                fig_compare = plot_stock_comparison(data1, ticker1, data2, ticker2)
                if fig_compare:
                     st.plotly_chart(fig_compare, use_container_width=True)
                else:
                     st.write("Stock Comparison Chart Not Available")


if __name__ == "__main__":
    main()
