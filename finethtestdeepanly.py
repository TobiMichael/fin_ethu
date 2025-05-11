import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
import spacy  # For basic NLP tasks

# Load a small English NLP model from spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.warning("Downloading en_core_web_sm model for spaCy. This might take a moment.")
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Set Streamlit theme to match app's theme
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

def interpret_rsi(rsi_value):
    """Provides a simple textual interpretation of the RSI."""
    if rsi_value is not None:
        if rsi_value > 70:
            return "The RSI suggests the stock may be overbought, potentially indicating a possibility of a price correction."
        elif rsi_value < 30:
            return "The RSI suggests the stock may be oversold, potentially indicating a possibility of a price increase."
        elif 50 < rsi_value <= 70:
            return "The RSI indicates an upward trend but is not yet in overbought territory."
        elif 30 <= rsi_value < 50:
            return "The RSI indicates a downward trend but is not yet in oversold territory."
        else:
            return "The RSI is in a neutral zone, suggesting no strong upward or downward momentum."
    return "RSI value is not available for interpretation."

def analyze_stock(ticker, start_date):
    """
    Analyzes a stock using yfinance, calculates moving averages and RSI,
    displays data, generates charts, and provides NLP interpretation of RSI.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for {ticker} from {start_date}")
            return None, None

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get financial data
        stock_info = yf.Ticker(ticker)
        financials = stock_info.financials
        cashflow = stock_info.cashflow
        dividends = stock_info.dividends

        start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)

        # Get revenue data
        if 'Total Revenue' in financials.index:
            revenue_data = financials.loc['Total Revenue']
            if revenue_data.index.tz is None:
                revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC')
            else:
                revenue_data.index = revenue_data.index.tz_convert('UTC')
            revenue_data = revenue_data[revenue_data.index >= start_date_utc]
        else:
            revenue_data = pd.Series()

        # Get dividend data
        dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC') if not dividends.empty and dividends.index.tz is None else dividends.index.tz_convert('UTC') if not dividends.empty else dividends.index
        dividends = dividends[dividends.index >= start_date_utc] if not dividends.empty else dividends

        # Get free cash flow data
        if 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
            if fcf_data.index.tz is None:
                fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
            else:
                fcf_data.index = fcf_data.index.tz_convert('UTC')
            fcf_data = fcf_data[fcf_data.index >= start_date_utc]
        else:
            fcf_data = pd.Series()

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)

        # NLP Interpretation
        latest_rsi = latest_data['RSI'].iloc[0] if not latest_data.empty else None
        rsi_interpretation = interpret_rsi(latest_rsi)

        fig, axes = plt.subplots(5, 1, figsize=(12, 18))

        # Subplot 1: Price and Moving Averages
        axes[0].plot(stock_data['Close'], label='Close Price')
        axes[0].plot(stock_data['50_MA'], label='50-Day MA')
        axes[0].plot(stock_data['200_MA'], label='200-Day MA')
        axes[0].set_title(f'{ticker} Price and Moving Averages from {start_date}')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].grid(True)

        # Subplot 2: RSI
        axes[1].plot(stock_data['RSI'], label='RSI', color='purple')
        axes[1].set_title(f'{ticker} RSI from {start_date}')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('RSI')
        axes[1].axhline(70, color='red', linestyle='--', label='Overbought (70)')
        axes[1].axhline(30, color='green', linestyle='--', label='Oversold (30)')
        axes[1].legend()
        axes[1].grid(True)

        # Subplot 3: Revenue (Bar Chart)
        if not revenue_data.empty:
            axes[2].bar(revenue_data.index, revenue_data.values, color='green', width=70)
            axes[2].set_title(f'{ticker} Revenue from {start_date}')
            axes[2].set_xlabel('Date')
            axes[2].set_ylabel('Revenue')
            axes[2].grid(axis='y')
        else:
            axes[2].text(0.5, 0.5, "Revenue Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[2].transAxes)

        # Subplot 4: Dividends (Bar Chart)
        if not dividends.empty:
            axes[3].bar(dividends.index, dividends.values, color='orange', width=70)
            axes[3].set_title(f'{ticker} Dividends from {start_date}')
            axes[3].set_xlabel('Date')
            axes[3].set_ylabel('Dividend Amount')
            axes[3].grid(axis='y')
        else:
            axes[3].text(0.5, 0.5, "Dividend Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[3].transAxes)

        # Subplot 5: Free Cash Flow (Bar Chart)
        if not fcf_data.empty:
            axes[4].bar(fcf_data.index, fcf_data.values, color='blue', width=70)
            axes[4].set_title(f'{ticker} Free Cash Flow from {start_date}')
            axes[4].set_xlabel('Date')
            axes[4].set_ylabel('Free Cash Flow')
            axes[4].grid(axis='y')
        else:
            axes[4].text(0.5, 0.5, "Free Cash Flow Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[4].transAxes)

        plt.tight_layout(pad=3.0)
        return fig, stock_info.info.get('longName', ticker), rsi_interpretation

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None, None

def main():
    st.title("Finance Enthusiast")

    if 'fig' not in st.session_state:
        st.session_state.fig = None
    if 'stock_name' not in st.session_state:
        st.session_state.stock_name = None
    if 'rsi_interpretation' not in st.session_state:
        st.session_state.rsi_interpretation = None

    with st.sidebar:
        st.header("Analysis Options")
        ticker = st.text_input("Enter stock ticker symbol (e.g., AAPL): ").upper()
        start_year = st.number_input("Enter start year:", min_value=1900, max_value=datetime.now().year, step=1, value=datetime.now().year - 5)
        if st.button("Analyze"):
            try:
                start_date_str = f"{start_year}-01-01"
                st.session_state.fig, st.session_state.stock_name, st.session_state.rsi_interpretation = analyze_stock(ticker, start_date_str)
            except Exception as e:
                st.error(f"An error occurred: {e}")

        st.sidebar.header("NLP Interpretation")
        if st.session_state.rsi_interpretation:
            st.sidebar.info(st.session_state.rsi_interpretation)
        else:
            st.sidebar.info("No NLP interpretation available yet. Please analyze a stock.")

    if st.session_state.fig:
        if st.session_state.stock_name:
            st.header(f'{st.session_state.stock_name} ({ticker})')
        st.pyplot(st.session_state.fig, use_container_width=True)
        st.session_state.fig = None
        st.session_state.stock_name = None
        st.session_state.rsi_interpretation = None

if __name__ == "__main__":
    main()
