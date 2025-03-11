import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Fetching data from a reliable source
def fetch_fed_rate_data():
    # Example dataset - Replace with actual data source or API call
    data = {
        'Date': pd.date_range(start='2000-01-01', end='2025-03-10', freq='AS'),
        'Rate': [6.5, 6.0, 1.75, 1.0, 2.0, 3.25, 0.0, 0.25, 0.5, 2.0, 2.25, 0.25, 0.1, 0.25, 0.75, 1.5, 2.5, 2.25, 4.5, 4.75, 5.0, 5.5, 5.0, 5.25, 5.5]
    }
    return pd.DataFrame(data)

# Streamlit app
def main():
    st.title("Federal Reserve Rate Chart (2000 - Present)")
    st.write("This app displays the Federal Reserve interest rates over time.")

    # Fetch and process data
    fed_data = fetch_fed_rate_data()
    fed_data['Date'] = pd.to_datetime(fed_data['Date'])
    
    # Plot the data
    st.line_chart(fed_data.set_index('Date'))

    # Display data table
    st.write("Interest Rate Data:")
    st.dataframe(fed_data)

if __name__ == '__main__':
    main()

