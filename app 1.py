import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
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
    displays data, and generates charts including revenue, dividends, and free cash flow.
    """
    try:
        stock_data = yf.download(ticker, start=start_date)

        if stock_data.empty:
            print(f"No data found for {ticker} from {start_date}")
            return None, None

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get financial data
        stock_info = yf.Ticker(ticker)
        financials = stock_info.financials

        # Get revenue data
        if 'Total Revenue' in financials.index:
            revenue_data = financials.loc['Total Revenue']
            if revenue_data.index.tz is None:
                revenue_data.index = pd.to_datetime(revenue_data.index).tz_localize('UTC')
            else:
                revenue_data.index = revenue_data.index.tz_convert('UTC')
            start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
            revenue_data = revenue_data[revenue_data.index >= start_date_utc]
        else:
            revenue_data = pd.Series()  # Empty series if revenue data is not available

        # Get dividend data
        dividends = stock_info.dividends
        if dividends.index.tz is None:
            dividends.index = pd.to_datetime(dividends.index).tz_localize('UTC')
        else:
            dividends.index = dividends.index.tz_convert('UTC')
        start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
        dividends = dividends[dividends.index >= start_date_utc]

        # Get free cash flow data
        cashflow = stock_info.cashflow
        if 'Free Cash Flow' in cashflow.index:
            fcf_data = cashflow.loc['Free Cash Flow']
            if fcf_data.index.tz is None:
                fcf_data.index = pd.to_datetime(fcf_data.index).tz_localize('UTC')
            else:
                fcf_data.index = fcf_data.index.tz_convert('UTC')
            start_date_utc = pd.to_datetime(start_date).tz_localize(pytz.utc)
            fcf_data = fcf_data[fcf_data.index >= start_date_utc]
        else:
            fcf_data = pd.Series()  # Empty series if FCF data is not available

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)

        print(f"\nAnalysis for {ticker} (Last Trading Day, from {start_date}):")
        print(latest_data)

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
        plt.show()
        return fig, stock_info.info.get('longName', ticker)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def main():
    # Get user input
    ticker = input("Enter stock ticker symbol (e.g., AAPL): ").upper()
    start_year = int(input(f"Enter start year (1900-{datetime.now().year}): "))
    
    # Validate input
    if start_year < 1900 or start_year > datetime.now().year:
        print(f"Invalid year. Please enter a year between 1900 and {datetime.now().year}.")
        return
    
    try:
        start_date_str = f"{start_year}-01-01"
        analyze_stock(ticker, start_date_str)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
