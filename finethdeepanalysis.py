import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    body {
        color: #333;
        background-color: #f0f2f6;
    }
    .stPlot {
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
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

def get_stock_data(ticker, start_date):
    """Downloads stock data from yfinance and calculates moving averages and RSI."""
    try:
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

def plot_stock_comparison(data1, ticker1, data2, ticker2, ax):
    """Plots the closing prices of two stocks for comparison on a given axis."""
    if data1 is None or data2 is None:
        st.warning("Could not plot comparison due to missing data.")
        return

    ax.plot(data1.index, data1['Close'], label=f'{ticker1} Close Price')
    ax.plot(data2.index, data2['Close'], label=f'{ticker2} Close Price')
    ax.set_title(f'Comparison of {ticker1} and {ticker2} Close Prices')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()
    ax.grid(True)

def analyze_stock(ticker, start_date):
    """
    Analyzes a single stock using yfinance, calculates moving averages and RSI,
    displays data, and generates charts including revenue, dividends, and free cash flow.
    Returns the Matplotlib figure and stock name.
    """
    try:
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
        if stock_info.cashflow is not None and 'Free Cash Flow' in stock_info.cashflow.index:
            fcf_data = stock_info.cashflow.loc['Free Cash Flow']
            if not fcf_data.empty:
                if fcf_data.index.tz is None:
                    fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
                else:
                    fcf_data.index = fcf_data.index.tz_convert('UTC')
                start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                fcf_data = fcf_data[fcf_data.index >= start_date_utc]

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)
        st.subheader(f"Analysis for {ticker} (Last Trading Day, from {start_date}):")
        st.dataframe(latest_data)

        fig, axes = plt.subplots(5, 1, figsize=(12, 18))

        # Subplot 1: Price and Moving Averages
        axes[0].plot(stock_data['Close'], label='Close Price')
        axes[0].plot(stock_data['50_MA'], label='50-Day MA')
        axes[0].plot(stock_data['200_MA'], label='200-Day MA')
        axes[0].set_title(f'{ticker} Price and Moving Averages')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].grid(True)

        # Subplot 2: RSI
        axes[1].plot(stock_data['RSI'], label='RSI', color='purple')
        axes[1].set_title(f'{ticker} RSI')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('RSI')
        axes[1].axhline(70, color='red', linestyle='--', label='Overbought (70)')
        axes[1].axhline(30, color='green', linestyle='--', label='Oversold (30)')
        axes[1].legend()
        axes[1].grid(True)

        # Subplot 3: Revenue (Bar Chart)
        if not revenue_data.empty:
            axes[2].bar(revenue_data.index, revenue_data.values, color='green', width=70)
            axes[2].set_title(f'{ticker} Revenue')
            axes[2].set_xlabel('Date')
            axes[2].set_ylabel('Revenue')
            axes[2].grid(axis='y')
        else:
            axes[2].text(0.5, 0.5, "Revenue Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[2].transAxes)

        # Subplot 4: Dividends (Bar Chart)
        if not dividends.empty:
            axes[3].bar(dividends.index, dividends.values, color='orange', width=70)
            axes[3].set_title(f'{ticker} Dividends')
            axes[3].set_xlabel('Date')
            axes[3].set_ylabel('Dividend Amount')
            axes[3].grid(axis='y')
        else:
            axes[3].text(0.5, 0.5, "Dividend Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[3].transAxes)

        # Subplot 5: Free Cash Flow (Bar Chart)
        if not fcf_data.empty:
            axes[4].bar(fcf_data.index, fcf_data.values, color='blue', width=70)
            axes[4].set_title(f'{ticker} Free Cash Flow')
            axes[4].set_xlabel('Date')
            axes[4].set_ylabel('Free Cash Flow')
            axes[4].grid(axis='y')
        else:
            axes[4].text(0.5, 0.5, "Free Cash Flow Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[4].transAxes)

        plt.tight_layout(pad=3.0)
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
                st.pyplot(fig1, use_container_width=True)

        with col2:
            st.subheader(f"Analysis for {ticker2}")
            fig2, name2 = analyze_stock(ticker2, start_date_str)
            if fig2:
                st.pyplot(fig2, use_container_width=True)

        # Optional: Display comparison chart below the columns
        data1 = get_stock_data(ticker1, start_date_str)
        data2 = get_stock_data(ticker2, start_date_str)
        if data1 is not None and data2 is not None:
            st.subheader("Comparison of Closing Prices")
            fig_compare, ax_compare = plt.subplots(figsize=(12, 6))
            plot_stock_comparison(data1, ticker1, data2, ticker2, ax_compare)
            st.pyplot(fig_compare, use_container_width=True)

if __name__ == "__main__":
    main()
