import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# Set Streamlit theme to match app's theme
st.set_page_config(layout="wide")

# Function to get text and background colors based on theme
def get_colors():
    is_dark_theme = st.config.get_option("theme.base") == "dark"
    text_color = "#FFFFFF" if is_dark_theme else "#333333"
    background_color = "#111111" if is_dark_theme else "#f0f2f6"
    return text_color, background_color

text_color, background_color = get_colors()

st.markdown(
    f"""
    <style>
    body {{
        color: {text_color};
        background-color: {background_color};
    }}
    .stPlot {{
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }}
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
    displays data, and generates charts including revenue and dividends.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for {ticker} from {start_date}")
            return None

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get revenue data
        stock_info = yf.Ticker(ticker)
        revenue_data = stock_info.financials.loc['Total Revenue']

        if revenue_data.index.tz is None:
            revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC')
        else:
            revenue_data.index = revenue_data.index.tz_convert('UTC')

        start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
        revenue_data = revenue_data[revenue_data.index >= start_date_utc]

        # Get dividend data
        dividends = stock_info.dividends

        if dividends.index.tz is None:
            dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC')
        else:
            dividends.index = dividends.index.tz_convert('UTC')

        dividends = dividends[dividends.index >= start_date_utc]

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)

        st.write(f"\nAnalysis for {ticker} (Last Trading Day, from {start_date}):")
        st.write(latest_data)

        fig, axes = plt.subplots(4, 1, figsize=(12, 14))

        # Subplot 1: Price and Moving Averages
        axes[0].plot(stock_data['Close'], label='Close Price')
        axes[0].plot(stock_data['50_MA'], label='50-Day MA')
        axes[0].plot(stock_data['200_MA'], label='200-Day MA')
        axes[0].set_title(f'{ticker} Price and Moving Averages from {start_date}', color=text_color)
        axes[0].set_xlabel('Date', color=text_color)
        axes[0].set_ylabel('Price', color=text_color)
        axes[0].tick_params(axis='x', colors=text_color)
        axes[0].tick_params(axis='y', colors=text_color)
        axes[0].legend(labelcolor=text_color)
        axes[0].grid(True)
        fig.patch.set_alpha(0)
        axes[0].patch.set_alpha(0)

        # Subplot 2: RSI
        axes[1].plot(stock_data['RSI'], label='RSI', color='purple')
        axes[1].set_title(f'{ticker} RSI from {start_date}', color=text_color)
        axes[1].set_xlabel('Date', color=text_color)
        axes[1].set_ylabel('RSI', color=text_color)
        axes[1].tick_params(axis='x', colors=text_color)
        axes[1].tick_params(axis='y', colors=text_color)
        axes[1].axhline(70, color='red', linestyle='--', label='Overbought (70)')
        axes[1].axhline(30, color='green', linestyle='--', label='Oversold (30)')
        axes[1].legend(labelcolor=text_color)
        axes[1].grid(True)
        axes[1].patch.set_alpha(0)

        # Subplot 3: Revenue
        if not revenue_data.empty:
            axes[2].plot(revenue_data.index, revenue_data.values, label='Revenue', color='green')
            axes[2].set_title(f'{ticker} Revenue from {start_date}', color=text_color)
            axes[2].set_xlabel('Date', color=text_color)
            axes[2].set_ylabel('Revenue', color=text_color)
            axes[2].tick_params(axis='x', colors=text_color)
            axes[2].tick_params(axis='y', colors=text_color)
            axes[2].legend(labelcolor=text_color)
            axes[2].grid(True)
            axes[2].patch.set_alpha(0)
        else:
            axes[2].text(0.5, 0.5, "Revenue Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[2].transAxes, color=text_color)

        # Subplot 4: Dividends
        if not dividends.empty:
            axes[3].plot(dividends.index, dividends.values, label='Dividends', color='orange', marker='o')
            axes[3].set_title(f'{ticker} Dividends from {start_date}', color=text_color)
            axes[3].set_xlabel('Date', color=text_color)
            axes[3].set_ylabel('Dividend Amount', color=text_color)
            axes[3].tick_params(axis='x', colors=text_color)
            axes[3].tick_params(axis='y', colors=text_color)
            axes[3].legend(labelcolor=text_color)
            axes[3].grid(True)
            axes[3].patch.set_alpha(0)
        else:
            axes[3].text(0.5, 0.5, "Dividend Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[3].transAxes, color=text_color)

        plt.tight_layout(pad=3.0)
        return fig, stock_info.info.get('longName', ticker)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

def main():
    st.title("Finance Enthusiast")

    if 'fig' not in st.session_state:
        st.session_state.fig = None
    if 'stock_name' not in st.session_state:
        st.session_state.stock_name = None

    with st.sidebar:
        ticker = st.text_input
