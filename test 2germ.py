import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

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
    displays data, and generates interactive charts including revenue, dividends, and free cash flow.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for {ticker} from {start_date}")
            return

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Display latest data
        st.subheader(f"Analysis for {ticker} (Last Trading Day, from {start_date}):")
        st.dataframe(stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1))

        # Create subplots
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
        if 'Total Revenue' in financials.index:
            revenue_data = financials.loc['Total Revenue']
            revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC') if revenue_data.index.tz is None else revenue_data.index.tz_convert('UTC')
            revenue_data = revenue_data[revenue_data.index >= start_date_utc]
            if not revenue_data.empty:
                fig.add_trace(go.Bar(x=revenue_data.index, y=revenue_data.values, name='Revenue', marker_color='green'), row=3, col=1)
                fig.update_yaxes(title_text="Revenue", row=3, col=1)
            else:
                fig.add_annotation(text="Revenue Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=3, col=1)
        else:
            fig.add_annotation(text="Revenue Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=3, col=1)

        # Subplot 4: Dividends (Bar Chart)
        if not dividends.empty:
            dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC') if dividends.index.tz is None else dividends.index.tz_convert('UTC')
            dividends = dividends[dividends.index >= start_date_utc]
            if not dividends.empty:
                fig.add_trace(go.Bar(x=dividends.index, y=dividends.values, name='Dividends', marker_color='orange'), row=4, col=1)
                fig.update_yaxes(title_text="Dividend Amount", row=4, col=1)
            else:
                fig.add_annotation(text="Dividend Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=4, col=1)
        else:
            fig.add_annotation(text="Dividend Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=4, col=1)

        # Subplot 5: Free Cash Flow (Bar Chart)
        if 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
            fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC') if fcf_data.index.tz is None else fcf_data.index.tz_convert('UTC')
            fcf_data = fcf_data[fcf_data.index >= start_date_utc]
            if not fcf_data.empty:
                fig.add_trace(go.Bar(x=fcf_data.index, y=fcf_data.values, name='Free Cash Flow', marker_color='blue'), row=5, col=1)
                fig.update_yaxes(title_text="Free Cash Flow", row=5, col=1)
            else:
                fig.add_annotation(text="Free Cash Flow Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=5, col=1)
        else:
            fig.add_annotation(text="Free Cash Flow Data Not Available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, row=5, col=1)

        fig.update_layout(height=1500, title_text=f"{stock_info.info.get('longName', ticker)} Analysis from {start_date}", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")

def main():
    st.title("Stock Analysis Web App")

    ticker = st.text_input("Enter stock ticker symbol (e.g., AAPL):").upper()
    start_year = st.number_input(f"Enter start year (1900-{datetime.now().year}):", min_value=1900, max_value=datetime.now().year, value=2020, step=1)

    if st.button("Analyze"):
        if not ticker:
            st.warning("Please enter a stock ticker symbol.")
            return
        if start_year < 1900 or start_year > datetime.now().year:
            st.error(f"Invalid year. Please enter a year between 1900 and {datetime.now().year}.")
            return

        start_date_str = f"{int(start_year)}-01-01"
        analyze_stock(ticker, start_date_str)

if __name__ == "__main__":
    main()
