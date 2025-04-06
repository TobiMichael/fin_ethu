import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# Set Streamlit theme to match app's theme
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    body {
        color: #333;
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_up = up.rolling(window).mean()
    average_down = down.rolling(window).mean()
    rs = average_up / average_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_stock(ticker, start_date):
    """
    Analyzes a stock using yfinance, calculates moving averages and RSI,
    displays data, and generates interactive charts including revenue, dividends, and free cash flow using Plotly.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for {ticker} from {start_date}")
            return None, None, None, None

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)
        st.write(f"\nAnalysis for {ticker} (Last Trading Day, from {start_date}):")
        st.write(latest_data)

        fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                            vertical_spacing=0.1,
                            subplot_titles=('Price and Moving Averages', 'RSI', 'Revenue', 'Dividends', 'Free Cash Flow'))

        # Subplot 1: Price and Moving Averages
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close Price'), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['50_MA'], name='50-Day MA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['200_MA'], name='200-Day MA'), row=1, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)

        # Subplot 2: RSI
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.add_hline(y=70, line=dict(color='red', dash='dash'), annotation_text="Overbought (70)", annotation_position="top right", row=2, col=1)
        fig.add_hline(y=30, line=dict(color='green', dash='dash'), annotation_text="Oversold (30)", annotation_position="bottom right", row=2, col=1)

        # Get financial data
        stock_info = yf.Ticker(ticker)
        financials = stock_info.financials
        cashflow = stock_info.cashflow
        dividends = stock_info.dividends

        start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)

        # Subplot 3: Revenue (Bar Chart)
        revenue_data = financials.loc['Total Revenue'] if 'Total Revenue' in financials.index else pd.Series()
        revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC') if not revenue_data.empty and revenue_data.index.tz is None else revenue_data.index.tz_convert('UTC') if not revenue_data.empty else revenue_data.index
        revenue_data = revenue_data[revenue_data.index >= start_date_utc] if not revenue_data.empty else revenue_data
        if not revenue_data.empty:
            fig.add_trace(go.Bar(x=revenue_data.index, y=revenue_data.values, name='Revenue', marker_color='green'), row=3, col=1)
            fig.update_yaxes(title_text="Revenue", row=3, col=1)
        else:
            fig.add_annotation(text="Revenue Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=3, col=1)

        # Subplot 4: Dividends (Bar Chart)
        dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC') if not dividends.empty and dividends.index.tz is None else dividends.index.tz_convert('UTC') if not dividends.empty else dividends.index
        dividends = dividends[dividends.index >= start_date_utc] if not dividends.empty else dividends
        if not dividends.empty:
            fig.add_trace(go.Bar(x=dividends.index, y=dividends.values, name='Dividends', marker_color='orange'), row=4, col=1)
            fig.update_yaxes(title_text="Dividend Amount", row=4, col=1)
        else:
            fig.add_annotation(text="Dividend Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=4, col=1)

        # Subplot 5: Free Cash Flow (Bar Chart)
        fcf_data = cashflow.loc['Free Cash Flow'] if 'Free Cash Flow' in cashflow.index else pd.Series()
        fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC') if not fcf_data.empty and fcf_data.index.tz is None else fcf_data.index.tz_convert('UTC') if not fcf_data.empty else fcf_data.index
        fcf_data = fcf_data[fcf_data.index >= start_date_utc] if not fcf_data.empty else fcf_data
        if not fcf_data.empty:
            fig.add_trace(go.Bar(x=fcf_data.index, y=fcf_data.values, name='Free Cash Flow', marker_color='blue'), row=5, col=1)
            fig.update_yaxes(title_text="Free Cash Flow", row=5, col=1)
        else:
            fig.add_annotation(text="Free Cash Flow Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=5, col=1)

        fig.update_layout(height=1500, showlegend=True)
        stock_name = stock_info.info.get('longName', ticker)
        return fig, stock_name

    except Exception as e:
        st.error(f"An error occurred for {ticker}: {e}")
        return None, None

def main():
    st.title("Finance Enthusiast - Compare Stocks")

    start_year = st.number_input("Enter start year:", min_value=1900, max_value=datetime.now().year, step=1, value=datetime.now().year - 5)
    start_date_str = f"{int(start_year)}-01-01"

    col1, col2 = st.columns(2)

    with col1:
        ticker1 = st.text_input("Enter first stock ticker symbol (e.g., AAPL):").upper()
        if ticker1:
            fig1, stock_name1 = analyze_stock(ticker1, start_date_str)
            if fig1:
                st.header(f'{stock_name1} ({ticker1})')
                st.plotly_chart(fig1, use_container_width=True)

    with col2:
        ticker2 = st.text_input("Enter second stock ticker symbol (e.g., GOOGL):").upper()
        if ticker2:
            fig2, stock_name2 = analyze_stock(ticker2, start_date_str)
            if fig2:
                st.header(f'{stock_name2} ({ticker2})')
                st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
