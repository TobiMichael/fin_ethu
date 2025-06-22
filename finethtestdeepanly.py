import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz


# Cache data to improve performance
@st.cache_data
def get_stock_data(ticker, start_date):
    """Downloads stock data from yfinance and calculates moving averages and RSI."""
    try:
        stock_data = yf.download(ticker, start=start_date)
        if stock_data.empty:
            st.warning(f"No data found for {ticker} from {start_date}")
            return None
        stock_data["50_MA"] = stock_data["Close"].rolling(window=50).mean()
        stock_data["200_MA"] = stock_data["Close"].rolling(window=200).mean()
        stock_data["RSI"] = calculate_rsi(stock_data)
        return stock_data
    except Exception as e:
        st.error(f"Error downloading data for {ticker}: {e}")
        return None


def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data["Close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    average_up = up.rolling(window).mean()
    average_down = down.rolling(window).mean()
    rs = average_up / average_down
    rsi = 100 - (100 / (1 + rs))
    return rsi


def plot_stock_comparison(data1, ticker1, data2, ticker2):
    """Plots the closing prices of two stocks for comparison."""
    if data1 is None or data2 is None:
        st.warning("Could not plot comparison due to missing data.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data1.index, y=data1["Close"], mode="lines", name=f"{ticker1} Close Price"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data2.index, y=data2["Close"], mode="lines", name=f"{ticker2} Close Price"
        )
    )
    fig.update_layout(
        title=f"Comparison of {ticker1} and {ticker2} Close Prices",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def analyze_stock(ticker, start_date):
    """
    Analyzes a single stock using yfinance, calculates moving averages and RSI,
    displays data, and generates charts including revenue, dividends, and free cash flow using Plotly.
    Returns the Plotly figure and stock name.
    """
    try:
        stock_data = get_stock_data(ticker, start_date)

        if stock_data is None:
            return None, None

        # Get financial data
        stock_info = yf.Ticker(ticker)
        try:
            financials = stock_info.financials
            dividends = stock_info.dividends
            cashflow = stock_info.cashflow
            info = stock_info.info
        except Exception as e:
            st.error(f"Error fetching financial data for {ticker}: {e}")
            return None, None

        # Helper function to process financial data
        def process_financial_data(data, data_type):
            if data is not None and not data.empty:
                if data.index.tz is None:
                    data.index = pd.to_datetime(data.index).tz_localize("UTC")
                else:
                    data.index = data.index.tz_convert("UTC")
                start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
                return data[data.index >= start_date_utc]
            else:
                st.info(f"{data_type} Data Not Available for {ticker}")
                return pd.Series()

        # Get revenue data
        revenue_data = pd.Series()
        if financials is not None and "Total Revenue" in financials.index:
            revenue_data = financials.loc["Total Revenue"]
            revenue_data = process_financial_data(revenue_data, "Revenue")

        # Get dividend data
        dividends = process_financial_data(dividends, "Dividend")

        # Get free cash flow data
        fcf_data = pd.Series()
        if cashflow is not None and "Free Cash Flow" in cashflow.index:
            fcf_data = cashflow.loc["Free Cash Flow"]
            fcf_data = process_financial_data(fcf_data, "Free Cash Flow")

        latest_data = stock_data[["Close", "50_MA", "200_MA", "RSI"]].tail(1)
        st.subheader(f"Analysis for {ticker} (Last Trading Day, from {start_date}):")
        st.dataframe(latest_data)

        # Create subplots
        fig = make_subplots(
            rows=5,
            cols=1,
            subplot_titles=(
                f"{ticker} Price and Moving Averages",
                f"{ticker} RSI",
                f"{ticker} Revenue",
                f"{ticker} Dividends",
                f"{ticker} Free Cash Flow",
            ),
        )

        # Subplot 1: Price and Moving Averages
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["Close"],
                mode="lines",
                name="Close Price",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["50_MA"],
                mode="lines",
                name="50-Day MA",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["200_MA"],
                mode="lines",
                name="200-Day MA",
            ),
            row=1,
            col=1,
        )

        # Subplot 2: RSI
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=stock_data["RSI"],
                mode="lines",
                name="RSI",
                marker_color="purple",
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=[70] * len(stock_data),
                mode="lines",
                name="Overbought (70)",
                marker_color="red",
                line=dict(dash="dash"),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=stock_data.index,
                y=[30] * len(stock_data),
                mode="lines",
                name="Oversold (30)",
                marker_color="green",
                line=dict(dash="dash"),
            ),
            row=2,
            col=1,
        )

        # Subplot 3: Revenue (Bar Chart)
        if not revenue_data.empty:
            fig.add_trace(
                go.Bar(
                    x=revenue_data.index,
                    y=revenue_data.values,
                    name="Revenue",
                    marker_color="green",
                ),
                row=3,
                col=1,
            )
        else:
            fig.add_annotation(
                text="Revenue Data Not Available",
                xref="x3 domain",
                yref="y3 domain",
                x=0.5,
                y=0.5,
                showarrow=False,
                row=3,
                col=1,
            )

        # Subplot 4: Dividends (Bar Chart)
        if not dividends.empty:
            fig.add_trace(
                go.Bar(
                    x=dividends.index,
                    y=dividends.values,
                    name="Dividends",
                    marker_color="orange",
                ),
                row=4,
                col=1,
            )
        else:
            fig.add_annotation(
                text="Dividend Data Not Available",
                xref="x4 domain",
                yref="y4 domain",
                x=0.5,
                y=0.5,
                showarrow=False,
                row=4,
                col=1,
            )

        # Subplot 5: Free Cash Flow (Bar Chart)
        if not fcf_data.empty:
            fig.add_trace(
                go.Bar(
                    x=fcf_data.index,
                    y=fcf_data.values,
                    name="Free Cash Flow",
                    marker_color="blue",
                ),
                row=5,
                col=1,
            )
        else:
            fig.add_annotation(
                text="Free Cash Flow Data Not Available",
                xref="x5 domain",
                yref="y5 domain",
                x=0.5,
                y=0.5,
                showarrow=False,
                row=5,
                col=1,
            )

        fig.update_layout(
            height=1800,
            title_text=f"{ticker} Financial Analysis",
            template="plotly_white",
        )

        return fig, info.get("longName", ticker)

    except Exception as e:
        st.error(f"An error occurred during analysis of {ticker}: {e}")
        return None, None


def main():
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
    st.title("Finance Enthusiast")

    col1, col2 = st.columns(2)

    with st.sidebar:
        st.header("Stock Analysis")
        ticker1 = st.text_input("Enter first stock ticker:", "AAPL").upper()
        ticker2 = st.text_input("Enter second stock ticker:", "GOOGL").upper()
        start_year = st.number_input(
            "Enter start year:",
            min_value=1900,
            max_value=datetime.now().year,
            step=1,
            value=datetime.now().year - 5,
        )
        analyze_button = st.button("Analyze Stocks")

    if analyze_button:
        start_date_str = f"{start_year}-01-01"

        with col1:
            st.subheader(f"Analysis for {ticker1}")
            fig1, name1 = analyze_stock(ticker1, start_date_str)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader(f"Analysis for {ticker2}")
            fig2, name2 = analyze_stock(ticker2, start_date_str)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)

        # Optional: Display comparison chart below the columns
        data1 = get_stock_data(ticker1, start_date_str)
        data2 = get_stock_data(ticker2, start_date_str)
        if data1 is not None and data2 is not None:
            st.subheader("Comparison of Closing Prices")
            plot_stock_comparison(data1, ticker1, data2, ticker2)


if __name__ == "__main__":
    main()
