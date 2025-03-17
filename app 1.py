import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Streamlit app title
st.title("Stock Price Viewer")

# EOD API configuration
api_key = "DEMO"  # Replace with your EOD API key
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL.US):", "AAPL.US")  # User input for ticker
start_date = st.date_input("Start Date", pd.to_datetime("2023-02-01"))  # User input for start date
end_date = st.date_input("End Date", pd.to_datetime("2023-03-01"))  # User input for end date

# Fetch stock data from EOD API
if st.button("Fetch Data"):  # Button to trigger data fetching
    url = f"https://eodhistoricaldata.com/api/eod/{ticker}?from={start_date}&to={end_date}&api_token={api_key}&fmt=json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        # Display the data as a table in Streamlit
        st.write("### Stock Data", df)

        # Plot the stock data
        st.write("### Closing Price Chart")
        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df['close'], label='Closing Price', color='blue')
        plt.title(f"{ticker} Stock Price ({start_date} to {end_date})")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid()

        # Render the plot in Streamlit
        st.pyplot(plt)
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
