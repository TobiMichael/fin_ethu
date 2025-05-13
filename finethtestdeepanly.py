import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# Removed the custom CSS styling block

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

def get_stock_data(ticker, start_date):
    """Downloads stock data from yfinance and calculates moving averages and RSI."""
    try:
        # yfinance automatically includes Open, High, Low, Close, Adj Close, Volume
        stock_data = yf.download(ticker, start=start_date)
        if stock_data.empty:
            st.warning(f"No data found for {ticker} from {start_date}")
            return None
        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)
        return stock_data
    except Exception as e:
        st.error(f"Error downloading data for {ticker}: {e}")
        return None

# Modified plot_stock_comparison function to use candlestick charts
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


def analyze_stock(ticker, start_date):
    """
    Analyzes a single stock using yfinance, calculates moving averages and RSI,
    displays data, and generates charts including revenue, dividends, and free cash flow using Plotly.
    Returns the Plotly figure and stock name.
    """
    try:
        # yfinance automatically includes Open, High, Low, Close, Adj Close, Volume
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.warning(f"No data found for {ticker} from {start_date}")
            return None, None

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get financial data
        stock_info = yf.Ticker(ticker)
        financials = stock_info.financials
        cashflow = stock_info.cashflow

        # Get revenue data
        revenue_data = pd.Series()
        if financials is not None and 'Total Revenue' in financials.index:
            revenue_data = financials.loc['Total Revenue']
            if not revenue_data.empty:
                 # Ensure index is datetime and timezone-aware (UTC)
                 if revenue_data.index.tz is None:
                     revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC')
                 else:
                     revenue_data.index = revenue_data.index.tz_convert('UTC')
                 start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                 revenue_data = revenue_data[revenue_data.index >= start_date_utc]


        # Get dividend data
        dividends = pd.Series()
        if stock_info.dividends is not None:
            dividends = stock_info.dividends
            if not dividends.empty:
                 # Ensure index is datetime and timezone-aware (UTC)
                 if dividends.index.tz is None:
                     dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC')
                 else:
                     dividends.index = dividends.index.tz_convert('UTC')
                 start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                 dividends = dividends[dividends.index >= start_date_utc]


        # Get free cash flow data
        fcf_data = pd.Series()
        if cashflow is not None and 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
            if not fcf_data.empty:
                 # Ensure index is datetime and timezone-aware (UTC)
                 if fcf_data.index.tz is None:
                     fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
                 else:
                     fcf_data.index = fcf_data.index.tz_convert('UTC')
                 start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                 fcf_data = fcf_data[fcf_data.index >= start_date_utc]


        # Display latest data including Open and Close
        latest_data = stock_data[['Open', 'High', 'Low', 'Close', '50_MA', '200_MA', 'RSI']].tail(1) # Added High, Low
        st.subheader(f"Analysis for {ticker} (Last Trading Day, from {start_date}):")
        st.dataframe(latest_data)

        # Create subplots: 5 rows, 1 column. Share x-axis for price and RSI.
        # Financial charts have their own x-axes as their dates might differ.
        fig = make_subplots(rows=5, cols=1,
                            shared_xaxes=False, # Set to False to allow different x-axes for financial data
                            subplot_titles=(f'{ticker} Price (Candlestick) and Moving Averages', # Updated title
                                            f'{ticker} RSI',
                                            f'{ticker} Revenue',
                                            f'{ticker} Dividends',
                                            f'{ticker} Free Cash Flow'),
                            vertical_spacing=0.08) # Adjust spacing between subplots

        # Subplot 1: Price (Candlestick) and Moving Averages
        # Replaced Scatter traces for Open/Close with a single Candlestick trace
        fig.add_trace(go.Candlestick(x=stock_data.index,
                                     open=stock_data['Open'],
                                     high=stock_data['High'],
                                     low=stock_data['Low'],
                                     close=stock_data['Close'],
                                     name='Price'),
                      row=1, col=1)

        # Keep the Moving Average traces
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['50_MA'], mode='lines', name='50-Day MA'),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['200_MA'], mode='lines', name='200-Day MA'),
                      row=1, col=1)

        # Subplot 2: RSI
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI', line=dict(color='purple')),
                      row=2, col=1)
        # Add horizontal lines for RSI levels
        fig.add_shape(type="line", x0=stock_data.index.min(), x1=stock_data.index.max(), y0=70, y1=70,
                      line=dict(color="red", width=2, dash="dash"), row=2, col=1)
        fig.add_shape(type="line", x0=stock_data.index.min(), x1=stock_data.index.max(), y0=30, y1=30,
                      line=dict(color="green", width=2, dash="dash"), row=2, col=1)
        fig.add_annotation(x=stock_data.index.max(), y=70, text="Overbought (70)", showarrow=False, yshift=10, row=2, col=1)
        fig.add_annotation(x=stock_data.index.max(), y=30, text="Oversold (30)", showarrow=False, yshift=-10, row=2, col=1)


        # Subplot 3: Revenue (Bar Chart)
        if not revenue_data.empty:
             fig.add_trace(go.Bar(x=revenue_data.index, y=revenue_data.values, name='Revenue', marker_color='green'),
                           row=3, col=1)
        else:
             # Add text annotation if data is not available
             fig.add_annotation(text="Revenue Data Not Available",
                                 xref="x3 domain", yref="y3 domain",
                                 x=0.5, y=0.5, showarrow=False, row=3, col=1)


        # Subplot 4: Dividends (Bar Chart)
        if not dividends.empty:
             fig.add_trace(go.Bar(x=dividends.index, y=dividends.values, name='Dividends', marker_color='orange'),
                           row=4, col=1)
        else:
             # Add text annotation if data is not available
             fig.add_annotation(text="Dividend Data Not Available",
                                 xref="x4 domain", yref="y4 domain",
                                 x=0.5, y=0.5, showarrow=False, row=4, col=1)


        # Subplot 5: Free Cash Flow (Bar Chart)
        if not fcf_data.empty:
             fig.add_trace(go.Bar(x=fcf_data.index, y=fcf_data.values, name='Free Cash Flow', marker_color='blue'),
                           row=5, col=1)
        else:
             # Add text annotation if data is not available
             fig.add_annotation(text="Free Cash Flow Data Not Available",
                                 xref="x5 domain", yref="y5 domain",
                                 x=0.5, y=0.5, showarrow=False, row=5, col=1)


        # Update layout for the entire figure
        fig.update_layout(
            height=1800, # Adjust height as needed
            title_text=f'Financial Analysis for {ticker}',
            hovermode='x unified' # Show tooltip for all traces at the same x-coordinate
        )

        # Update y-axis titles for each subplot
        fig.update_yaxes(title_text='Price', row=1, col=1)
        fig.update_yaxes(title_text='RSI', row=2, col=1)
        fig.update_yaxes(title_text='Revenue', row=3, col=1)
        fig.update_yaxes(title_text='Dividend Amount', row=4, col=1)
        fig.update_yaxes(title_text='Free Cash Flow', row=5, col=1)

        # Update x-axis titles for each subplot (only needed if not shared)
        fig.update_xaxes(title_text='Date', row=1, col=1)
        fig.update_xaxes(title_text='Date', row=2, col=1)
        fig.update_xaxes(title_text='Date', row=3, col=1)
        fig.update_xaxes(title_text='Date', row=4, col=1)
        fig.update_xaxes(title_text='Date', row=5, col=1)


        return fig, stock_info.info.get('longName', ticker)

    except Exception as e:
        st.error(f"An error occurred during analysis of {ticker}: {e}")
        return None, None


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

        with col1:
            st.subheader(f"Analysis for {ticker1}")
            fig1, name1 = analyze_stock(ticker1, start_date_str)
            if fig1:
                # Place the analysis chart in an expander
                with st.expander(f"### {ticker1} Financial Analysis"):
                    st.plotly_chart(fig1, use_container_width=True)


        with col2:
            st.subheader(f"Analysis for {ticker2}")
            fig2, name2 = analyze_stock(ticker2, start_date_str)
            if fig2:
                 # Place the analysis chart in an expander
                with st.expander(f"### {ticker2} Financial Analysis"):
                    st.plotly_chart(fig2, use_container_width=True)


        # Optional: Display comparison chart below the columns
        data1 = get_stock_data(ticker1, start_date_str)
        data2 = get_stock_data(ticker2, start_date_str)
        if data1 is not None and data2 is not None:
            # Place the comparison chart in an expander
            with st.expander("### Stock Price Comparison"):
                st.subheader("Comparison of Candlestick Prices") # Updated title
                fig_compare = plot_stock_comparison(data1, ticker1, data2, ticker2)
                if fig_compare:
                     st.plotly_chart(fig_compare, use_container_width=True)


if __name__ == "__main__":
    main()
