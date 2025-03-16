import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Fetching data from a reliable source
def fetch_fed_rate_data():
    try:
        # Example dataset - Replace with actual data source or API call
        data = {
            'Date': pd.date_range(start='2000-01-01', end='2025-03-10', freq='AS'),
            'Rate': [6.5, 6.0, 1.75, 1.0, 2.0, 3.25, 0.0, 0.25, 0.5, 2.0, 2.25, 0.25, 
                     0.1, 0.25, 0.75, 1.5, 2.5, 2.25, 4.5, 4.75, 5.0, 5.5, 5.0, 5.25, 5.5]
        }

        # Ensure lengths of all data arrays match
        if len(data['Date']) != len(data['Rate']):
            raise ValueError("Data arrays have mismatched lengths.")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error fetching Federal Reserve rate data: {e}")
        return pd.DataFrame()  # Return empty DataFrame in case of an error

# Streamlit app
def main():
    st.title("Federal Reserve Rate Chart (2000 - Present)")
    st.write("This app displays the Federal Reserve interest rates over time.")

    # Fetch and process data
    fed_data = fetch_fed_rate_data()
    
    if not fed_data.empty:
        fed_data['Date'] = pd.to_datetime(fed_data['Date'])
        
        # Plot the data
        st.line_chart(fed_data.set_index('Date'))

        # Display data table
        st.write("Interest Rate Data:")
        st.dataframe(fed_data)
    else:
        st.warning("No data available to display.")

if __name__ == '__main__':
    main()


