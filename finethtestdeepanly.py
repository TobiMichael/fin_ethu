import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Still needed for potential future use or if we decide to group some
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


# Modified analyze_stock function to return a dictionary of individual figures
def analyze_stock(ticker, start_date):
    """
    Analyzes a single stock using yfinance, calculates moving averages and RSI,
    displays data, and generates individual charts for price/MA, RSI, revenue,
    dividends, and free cash flow using Plotly.
    Returns a dictionary of Plotly figures and the stock name.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.warning(f"No data found for {ticker} from {start_date}")
            return {}, None # Return empty dict and None name

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
                 if fcf_data.index.tz is None:
                     fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
                 else:
                     fcf_data.index = fcf_data.index.tz_convert('UTC')
                 start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                 fcf_data = fcf_data[fcf_data.index >= start_date_utc]


        # Display latest data
        latest_data = stock_data[['Open', 'High', 'Low', 'Close', '50_MA', '200_MA', 'RSI']].tail(1)
        st.subheader(f"Analysis for {ticker} (Last Trading Day, from {start_date}):")
        st.dataframe(latest_data)

        # Create individual figures for each chart type
        charts = {}

        # Chart 1: Price (Candlestick) and Moving Averages
        fig_price_ma = go.Figure()
        fig_price_ma.add_trace(go.Candlestick(x=stock_data.index,
                                              open=stock_data['Open'],
                                              high=stock_data['High'],
                                              low=stock_data['Low'],
                                              close=stock_data['Close'],
                                              name='Price'))
        fig_price_ma.add_trace(go.Scatter(x=stock_data.index, y=stock_data['50_MA'], mode='lines', name='50-Day MA'))
        fig_price_ma.add_trace(go.Scatter(x=stock_data.index, y=stock_data['200_MA'], mode='lines', name='200-Day MA'))
        fig_price_ma.update_layout(title=f'{ticker} Price (Candlestick) and Moving Averages',
                                   xaxis_title='Date', yaxis_title='Price', hovermode='x unified',
                                   xaxis_rangeslider_visible=False) # Hide rangeslider for cleaner look
        charts['Price_MA'] = fig_price_ma

        # Chart 2: RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
        fig_rsi.add_shape(type="line", x0=stock_data.index.min(), x1=stock_data.index.max(), y0=70, y1=70, line=dict(color="red", width=2, dash="dash"))
        fig_rsi.add_shape(type="line", x0=stock_data.index.min(), x1=stock_data.index.max(), y0=30, y1=30, line=dict(color="green", width=2, dash="dash"))
        fig_rsi.add_annotation(x=stock_data.index.max(), y=70, text="Overbought (70)", showarrow=False, yshift=10)
        fig_rsi.add_annotation(x=stock_data.index.max(), y=30, text="Oversold (30)", showarrow=False, yshift=-10)
        fig_rsi.update_layout(title=f'{ticker} RSI', xaxis_title='Date', yaxis_title='RSI', hovermode='x unified')
        charts['RSI'] = fig_rsi

        # Chart 3: Revenue (Bar Chart)
        fig_revenue = go.Figure()
        if not revenue_data.empty:
             fig_revenue.add_trace(go.Bar(x=revenue_data.index, y=revenue_data.values, name='Revenue', marker_color='green'))
             fig_revenue.update_layout(title=f'{ticker} Revenue', xaxis_title='Date', yaxis_title='Revenue')
        else:
             fig_revenue.add_annotation(text="Revenue Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
             fig_revenue.update_layout(title=f'{ticker} Revenue (Data Not Available)')
        charts['Revenue'] = fig_revenue


        # Chart 4: Dividends (Bar Chart)
        fig_dividends = go.Figure()
        if not dividends.empty:
             fig_dividends.add_trace(go.Bar(x=dividends.index, y=dividends.values, name='Dividends', marker_color='orange'))
             fig_dividends.update_layout(title=f'{ticker} Dividends', xaxis_title='Date', yaxis_title='Dividend Amount')
        else:
             fig_dividends.add_annotation(text="Dividend Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
             fig_dividends.update_layout(title=f'{ticker} Dividends (Data Not Available)')
        charts['Dividends'] = fig_dividends


        # Chart 5: Free Cash Flow (Bar Chart)
        fig_fcf = go.Figure()
        if not fcf_data.empty:
             fig_fcf.add_trace(go.Bar(x=fcf_data.index, y=fcf_data.values, name='Free Cash Flow', marker_color='blue'))
             fig_fcf.update_layout(title=f'{ticker} Free Cash Flow', xaxis_title='Date', yaxis_title='Free Cash Flow')
        else:
             fig_fcf.add_annotation(text="Free Cash Flow Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
             fig_fcf.update_layout(title=f'{ticker} Free Cash Flow (Data Not Available)')
        charts['FCF'] = fig_fcf


        return charts, stock_info.info.get('longName', ticker)

    except Exception as e:
        st.error(f"An error occurred during analysis of {ticker}: {e}")
        return {}, None # Return empty dict and None name


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
            charts1, name1 = analyze_stock(ticker1, start_date_str)
            if charts1: # Check if charts dictionary is not empty
                # Place each chart in an expander
                chart_order = ['Price_MA', 'RSI', 'Revenue', 'Dividends', 'FCF'] # Define order for display
                chart_titles = {
                    'Price_MA': 'Price (Candlestick) and Moving Averages',
                    'RSI': 'Relative Strength Index (RSI)',
                    'Revenue': 'Revenue',
                    'Dividends': 'Dividends',
                    'FCF': 'Free Cash Flow'
                }
                for chart_key in chart_order:
                    # Set expanded=True if the chart figure exists (data is available)
                    expanded_state = chart_key in charts1 and charts1[chart_key] is not None and not charts1[chart_key].data == () # Check if figure has data traces
                    with st.expander(f"### {ticker1} - {chart_titles[chart_key]}", expanded=expanded_state):
                        if chart_key in charts1 and charts1[chart_key] is not None:
                             # Check if the figure has data before plotting
                             if charts1[chart_key].data:
                                st.plotly_chart(charts1[chart_key], use_container_width=True)
                             else:
                                 # Display placeholder if data was not available when creating the figure
                                 st.write(f"{chart_titles[chart_key]} Data Not Available")
                        elif chart_key in chart_titles: # Display placeholder if chart key not in charts dict (shouldn't happen with current logic)
                             st.write(f"{chart_titles[chart_key]} Data Not Available")


        with col2:
            st.subheader(f"Analysis for {ticker2}")
            charts2, name2 = analyze_stock(ticker2, start_date_str)
            if charts2: # Check if charts dictionary is not empty
                # Place each chart in an expander
                chart_order = ['Price_MA', 'RSI', 'Revenue', 'Dividends', 'FCF'] # Define order for display
                chart_titles = {
                    'Price_MA': 'Price (Candlestick) and Moving Averages',
                    'RSI': 'Relative Strength Index (RSI)',
                    'Revenue': 'Revenue',
                    'Dividends': 'Dividends',
                    'FCF': 'Free Cash Flow'
                }
                for chart_key in chart_order:
                    # Set expanded=True if the chart figure exists (data is available)
                    expanded_state = chart_key in charts2 and charts2[chart_key] is not None and not charts2[chart_key].data == () # Check if figure has data traces
                    with st.expander(f"### {ticker2} - {chart_titles[chart_key]}", expanded=expanded_state):
                         if chart_key in charts2 and charts2[chart_key] is not None:
                             # Check if the figure has data before plotting
                             if charts2[chart_key].data:
                                st.plotly_chart(charts2[chart_key], use_container_width=True)
                             else:
                                 # Display placeholder if data was not available when creating the figure
                                 st.write(f"{chart_titles[chart_key]} Data Not Available")
                         elif chart_key in chart_titles: # Display placeholder if chart key not in charts dict (shouldn't happen with current logic)
                             st.write(f"{chart_titles[chart_key]} Data Not Available")


        # Optional: Display comparison chart below the columns
        data1 = get_stock_data(ticker1, start_date_str)
        data2 = get_stock_data(ticker2, start_date_str)
        if data1 is not None and data2 is not None:
            # Place the comparison chart in an expander
            # Set expanded=True if the comparison figure exists and has data
            fig_compare = plot_stock_comparison(data1, ticker1, data2, ticker2)
            expanded_compare_state = fig_compare is not None and not fig_compare.data == ()
            with st.expander("### Stock Price Comparison", expanded=expanded_compare_state):
                st.subheader("Comparison of Candlestick Prices") # Updated title
                if fig_compare:
                    if fig_compare.data:
                        st.plotly_chart(fig_compare, use_container_width=True)
                    else:
                        st.write("Stock Comparison Chart Not Available")
                else:
                     st.write("Stock Comparison Chart Not Available")


if __name__ == "__main__":
    main()
