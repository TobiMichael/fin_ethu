import pandas as pd  # Ensure pandas is imported for date conversion
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt

# Streamlit app
def main():
    st.title("Apple Stock Price Viewer")
    st.write("This app fetches Apple (AAPL) stock data from Yahoo Finance and visualizes it.")

    # Set the date range
    start_date = st.date_input("Start date", value=pd.to_datetime("2000-01-01"))
    end_date = st.date_input("End date", value=pd.to_datetime("today"))

    # Fetch stock data
    try:
        st.write(f"Fetching Apple stock data from **{start_date}** to **{end_date}**...")
        stock_data = yf.download("AAPL", start=start_date, end=end_date)

        if not stock_data.empty:
            # Clean the stock data (ensure there are no missing values)
            stock_data.dropna(inplace=True)

            # Plot stock data
            st.write("### Apple Stock Closing Price Chart")
            plt.figure(figsize=(12, 6))
            plt.plot(stock_data.index, stock_data['Close'], label='Apple Stock Price', color='blue')
            plt.title("Apple Stock Prices Over Time", fontsize=16)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Closing Price (USD)", fontsize=12)
            plt.legend(loc="upper left")
            plt.grid(visible=True, linestyle='--', alpha=0.5)
            st.pyplot(plt)  # Display the plot using Streamlit

            # Show raw data
            st.write("### Raw Stock Data")
            st.dataframe(stock_data)
        else:
            st.warning("No data available for the selected date range. Please try again.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
