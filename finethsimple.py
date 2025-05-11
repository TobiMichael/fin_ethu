import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

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
            print(f"No data found for {ticker} from {start_date}")
            return

        stock_data['50_MA'] = stock_data['Close'].rolling(window=50).mean()
        stock_data['200_MA'] = stock_data['Close'].rolling(window=200).mean()
        stock_data['RSI'] = calculate_rsi(stock_data)

        # Get revenue data
        stock_info = yf.Ticker(ticker)
        revenue_data = stock_info.financials.loc['Total Revenue']
        revenue_data.index = pd.to_datetime(revenue_data.index)
        revenue_data = revenue_data.sort_index()

        # Get dividend data
        dividends = stock_info.dividends
        dividends.index = pd.to_datetime(dividends.index)

        latest_data = stock_data[['Close', '50_MA', '200_MA', 'RSI']].tail(1)

        print(f"\nAnalysis for {ticker} (Last Trading Day, from {start_date}):")
        print(latest_data.to_string())

        plt.figure(figsize=(12, 14)) #Increase figure height to accomodate 4 subplots

        # Subplot 1: Price and Moving Averages
        plt.subplot(4, 1, 1) #4 rows, 1 colum, subplot 1
        plt.plot(stock_data['Close'], label='Close Price')
        plt.plot(stock_data['50_MA'], label='50-Day MA')
        plt.plot(stock_data['200_MA'], label='200-Day MA')
        plt.title(f'{ticker} Price and Moving Averages from {start_date}')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)

        # Subplot 2: RSI
        plt.subplot(4, 1, 2) #4 rows, 1 column, subplot 2
        plt.plot(stock_data['RSI'], label='RSI', color='purple')
        plt.title(f'{ticker} RSI from {start_date}')
        plt.xlabel('Date')
        plt.ylabel('RSI')
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        plt.legend()
        plt.grid(True)

        # Subplot 3: Revenue
        plt.subplot(4, 1, 3) #4 rows, 1 column, subplot 3
        if not revenue_data.empty:
            plt.plot(revenue_data.index, revenue_data.values, label='Revenue', color='green')
            plt.title(f'{ticker} Revenue')
            plt.xlabel('Date')
            plt.ylabel('Revenue')
            plt.legend()
            plt.grid(True)
        else:
            plt.text(0.5, 0.5, "Revenue Data Not Available", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)

        # Subplot 4: Dividends
        plt.subplot(4, 1, 4) #4 rows, 1 column, subplot 4
        if not dividends.empty:
            plt.plot(dividends.index, dividends.values, label='Dividends', color='orange', marker='o')
            plt.title(f'{ticker} Dividends')
            plt.xlabel('Date')
            plt.ylabel('Dividend Amount')
            plt.legend()
            plt.grid(True)
        else:
            plt.text(0.5, 0.5, "Dividend Data Not Available", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")

ticker = input("Enter stock ticker symbol (e.g., AAPL): ").upper()
start_date_str = input("Enter start date (YYYY-MM-DD): ")

try:
    datetime.strptime(start_date_str, '%Y-%m-%d')
    analyze_stock(ticker, start_date_str)
except ValueError:
    print("Invalid date format. Please use %Y-%m-%d.")
except Exception as e:
    print(f"An error occurred: {e}")
