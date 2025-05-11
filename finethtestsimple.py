import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz # Import pytz for timezone handling

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Apply custom CSS for styling
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
    /* Style for the suggested ticker display */
    .suggested-ticker {
        background-color: #e9e9e9;
        padding: 8px;
        border-radius: 4px;
        margin-top: 10px;
        font-family: monospace;
        font-size: 1em;
        border: 1px solid #ccc;
        word-break: break-all; /* Prevent long tickers/names from overflowing */
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
    # Avoid division by zero in rs calculation
    # Replace 0 with a very small number (e.g., 1e-9) to prevent division by zero
    rs = average_up / average_down.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Provided function to attempt ticker lookup by potential name/ticker
def find_ticker_and_name(query):
    """Attempts to find a ticker and company name from a query string using yfinance."""
    if not query:
        return None, None

    # Try treating the query as a direct ticker first
    ticker_obj = yf.Ticker(query.upper())
    try:
        # Fetch info to validate the ticker and get the name
        # Checking for 'regularMarketPrice' or 'marketCap' is a good way to see if the ticker is valid and has data
        info = ticker_obj.info
        if info and (info.get('regularMarketPrice') is not None or info.get('marketCap') is not None):
             # If valid, return the ticker and its long name
             return query.upper(), info.get('longName', query.upper())
        else:
             # If direct ticker didn't work or no price/marketCap info, it might be a name (though yfinance lookup by name is unreliable)
             pass # Proceeding here won't magically make name search work well with yfinance
    except Exception as e:
        # print(f"Direct ticker lookup failed for {query}: {e}") # Optional: for debugging
        pass # It's likely not a direct valid ticker, might be a company name, but yfinance can't reliably search by name.

    # --- Limitation Acknowledged ---
    # yfinance does NOT have a robust function to search for tickers by company name.
    # A proper name-to-ticker search with suggestions requires a dedicated financial data API
    # or a pre-compiled, searchable database, which is beyond the scope of this script
    # using only yfinance.
    # Therefore, the primary method here is validating if the input IS a ticker.

    # If no valid ticker was found from the direct attempt
    return None, None

# Provided and completed function to analyze stock
def analyze_stock(ticker, start_date):
    """
    Analyzes a stock using yfinance, calculates moving averages and RSI,
    displays data, and generates charts including revenue, dividends, and free cash flow.
    """
    try:
        # Check if the ticker is empty before downloading
        if not ticker:
             st.warning("Please enter a ticker symbol to analyze.")
             return None, None

        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            st.error(f"No data found for ticker **{ticker}** from **{start_date}**. Please check the ticker symbol and date range.")
            return None, None

        # Calculate indicators
        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get company info, financials, and cash flow
        stock_info = yf.Ticker(ticker)
        info = stock_info.info # Get the info dictionary once
        financials = stock_info.financials
        cashflow = stock_info.cashflow
        long_name = info.get('longName', ticker) # Get the long name, default to ticker

        # Helper function to process financial/cashflow data (handles timezones)
        def process_financial_data(data_series, start_date):
             if data_series.empty:
                  return pd.Series()
             try:
                 # Attempt to localize if index is naive
                 if data_series.index.tz is None:
                      data_series.index = pd.to_datetime(data_series.index).tz_localize('UTC')
                 # Convert to UTC if already timezone-aware but not UTC
                 elif data_series.index.tz != pytz.utc:
                       data_series.index = data_series.index.tz_convert('UTC')
             except Exception as e:
                 st.warning(f"Could not process date index for financial data: {e}. Skipping timezone conversion.")
                 # Fallback: keep index as is if conversion fails

             start_date_utc = pd.to_datetime(start_date)
             # Ensure start_date_utc is timezone-aware for comparison if data_series index is aware
             if data_series.index.tz is not None:
                 start_date_utc = start_date_utc.tz_localize(pytz.utc)

             return data_series[data_series.index >= start_date_utc].sort_index()


        # Get revenue data
        revenue_data = pd.Series()
        if 'Total Revenue' in financials.index:
             revenue_data = financials.loc['Total Revenue']
             revenue_data = process_financial_data(revenue_data, start_date)


        # Get dividend data
        dividends = stock_info.dividends
        dividends = process_financial_data(dividends, start_date)


        # Get free cash flow data
        fcf_data = pd.Series()
        if 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
            fcf_data = process_financial_data(fcf_data, start_date)


        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)

        st.write(f"**Latest Data for {long_name} ({ticker})** (as of last trading day within the selected range):")
        st.write(latest_data)

        fig, axes = plt.subplots(5, 1, figsize=(12, 18))

        # Subplot 1: Price and Moving Averages
        axes[0].plot(stock_data.index, stock_data['Close'], label='Close Price')
        axes[0].plot(stock_data.index, stock_data['50_MA'], label='50-Day MA')
        axes[0].plot(stock_data.index, stock_data['200_MA'], label='200-Day MA')
        axes[0].set_title(f'{long_name} ({ticker}) Price and Moving Averages from {start_date}')
        axes[0].set_xlabel('Date')
        axes[0].set_ylabel('Price (<span class="math-inline">\)'\)
axes\[0\]\.legend\(\)
axes\[0\]\.grid\(True\)
\# Subplot 2\: RSI
axes\[1\]\.plot\(stock\_data\.index, stock\_data\['RSI'\], label\='RSI', color\='purple'\)
axes\[1\]\.set\_title\(f'\{long\_name\} \(\{ticker\}\) RSI from \{start\_date\}'\)
axes\[1\]\.set\_xlabel\('Date'\)
axes\[1\]\.set\_ylabel\('RSI'\)
axes\[1\]\.axhline\(70, color\='red', linestyle\='\-\-', label\='Overbought \(70\)'\)
axes\[1\]\.axhline\(30, color\='green', linestyle\='\-\-', label\='Oversold \(30\)'\)
axes\[1\]\.legend\(\)
axes\[1\]\.grid\(True\)
\# Subplot 3\: Revenue \(Bar Chart\)
if not revenue\_data\.empty\:
axes\[2\]\.bar\(revenue\_data\.index\.to\_numpy\(\), revenue\_data\.values, color\='green', width\=70\)
axes\[2\]\.set\_title\(f'\{long\_name\} \(\{ticker\}\) Revenue from \{start\_date\}'\)
axes\[2\]\.set\_xlabel\('Date'\)
axes\[2\]\.set\_ylabel\('Revenue \(</span>)')
            axes[2].grid(axis='y')
            fig.autofmt_xdate(axes=axes[2]) # Auto format date labels
        else:
            axes[2].text(0.5, 0.5, "Revenue Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[2].transAxes)
            axes[2].set_title(f'{long_name} ({ticker}) Revenue') # Still show title even if empty
            axes[2].set_xlabel('Date')
            axes[2].set_ylabel('Revenue (<span class="math-inline">\)'\)
\# Subplot 4\: Dividends \(Bar Chart\)
if not dividends\.empty\:
axes\[3\]\.bar\(dividends\.index\.to\_numpy\(\), dividends\.values, color\='orange', width\=70\)
axes\[3\]\.set\_title\(f'\{long\_name\} \(\{ticker\}\) Dividends from \{start\_date\}'\)
axes\[3\]\.set\_xlabel\('Date'\)
axes\[3\]\.set\_ylabel\('Dividend Amount \(</span>)')
            axes[3].grid(axis='y')
            fig.autofmt_xdate(axes=axes[3]) # Auto format date labels
        else:
            axes[3].text(0.5, 0.5, "Dividend Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[3].transAxes)
            axes[3].set_title(f'{long_name} ({ticker}) Dividends') # Still show title even if empty
            axes[3].set_xlabel('Date')
            axes[3].set_ylabel('Dividend Amount (<span class="math-inline">\)'\)
\# Subplot 5\: Free Cash Flow \(Bar Chart\)
if not fcf\_data\.empty\:
axes\[4\]\.bar\(fcf\_data\.index\.to\_numpy\(\), fcf\_data\.values, color\='blue', width\=70\)
axes\[4\]\.set\_title\(f'\{long\_name\} \(\{ticker\}\) Free Cash Flow from \{start\_date\}'\)
axes\[4\]\.set\_xlabel\('Date'\)
axes\[4\]\.set\_ylabel\('Free Cash Flow \(</span>)')
            axes[4].grid(axis='y')
            fig.autofmt_xdate(axes=axes[4]) # Auto format date labels
        else:
            axes[4].text(0.5, 0.5, "Free Cash Flow Data Not Available", horizontalalignment='center', verticalalignment='center', transform=axes[4].transAxes)
            axes[4].set_title(f'{long_name} ({ticker}) Free Cash Flow') # Still show title even if empty
            axes[4].set_xlabel('Date')
            axes[4].set_ylabel('Free Cash Flow ($)')


        plt.tight_layout(pad=3.0)
        return fig, long_name

    except Exception as e:
        st.error(f"An error occurred while fetching data for **{ticker}**: {e}. Please verify the ticker symbol and date range.")
        return None, None

def main():
    st.title("Finance Enthusiast")

    # Initialize session state variables
    if 'fig' not in st.session_state:
        st.session_state.fig = None
    if 'stock_name' not in st.session_state:
        st.session_state.stock_name = None
    if 'current_ticker' not in st.session_state:
        st.session_state.current_ticker = "" # The ticker currently being displayed/analyzed
    if 'suggested_ticker' not in st.session_state:
        st.session_state.suggested_ticker = None
    if 'suggested_name' not in st.session_state:
        st.session_state.suggested_name = None


    with st.sidebar:
        st.header("Find Ticker")

        # Input field for potential company name or ticker to lookup
        query = st.text_input(
            "Enter company name or ticker:",
            placeholder="e.g., Apple, Microsoft, TSLA",
            help="Enter the company name or ticker symbol to find the official ticker.",
            key="query_input"
        ).strip() # Remove leading/trailing whitespace

        # Button to trigger the lookup
        lookup_button = st.button("Find Ticker", key="lookup_button")

        # Display the suggested ticker and name if found
        if st.session_state.suggested_ticker:
            st.markdown(f"**Suggested Ticker:** <div class='suggested-ticker'>{st.session_state.suggested_ticker} ({st.session_state.suggested_name})</div>", unsafe_allow_html=True)
            st.info(f"Proceed to 'Analyze Stock' below using ticker: **{st.session_state.suggested_ticker}**")

        st.markdown("---") # Separator

        st.header("Analyze Stock")
        # Input for the confirmed ticker to analyze (can be manually entered or pre-filled from suggestion)
        ticker_to_analyze = st.text_input(
             "Ticker Symbol:",
             value=st.session_state.suggested_ticker if st.session_state.suggested_ticker else "", # Pre-fill if suggested
             placeholder="Enter Ticker (e.g., AAPL)",
             help="Enter or confirm the ticker symbol for analysis.",
             key="ticker_to_analyze_input"
        ).upper() # Convert to upper automatically


        start_year = st.number_input(
            "Enter start year:",
            min_value=1900,
            max_value=datetime.now().year,
            step=1,
            value=datetime.now().year - 5,
            key="start_year_input_analyze" # Unique key
        )

        analyze_button = st.button("Analyze Stock", key="analyze_button_main")

        st.markdown("---") # Separator

        # Add a clear button
        clear_button = st.button("Clear Results", key="clear_button_main")


    # Logic to handle the "Find Ticker" button click
    # This part runs outside the sidebar with block but is triggered by the sidebar button
    if lookup_button and query:
        # Clear previous suggestion and results when a new lookup is attempted
        st.session_state.suggested_ticker = None
        st.session_state.suggested_name = None
        st.session_state.fig = None
        st.session_state.stock_name = None
        st.session_state.current_ticker = ""

        st.info(f"Attempting to find ticker for '{query}'...")
        found_ticker, found_name = find_ticker_and_name(query)

        if found_ticker:
            st.session_state.suggested_ticker = found_ticker
            st.session_state.suggested_name = found_name
            # Rerun the app to update the sidebar with the suggestion
            st.experimental_rerun()
        else:
            st.warning(f"Could not find a valid ticker for '{query}'. Please try a different name or enter the exact ticker symbol.")
            st.session_state.suggested_ticker = None
            st.session_state.suggested_name = None
