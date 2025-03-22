def interpret_data(stock_data):
    """Provides insights into RSI, moving averages, and the latest closing price."""
    insights = []
    latest_close = stock_data['Close'].iloc[-1]
    rsi = stock_data['RSI'].iloc[-1]
    ma50 = stock_data['50_MA'].iloc[-1]
    ma200 = stock_data['200_MA'].iloc[-1]

    # RSI Interpretation
    if rsi > 70:
        insights.append("RSI indicates the stock is overbought, which could suggest a price correction soon.")
    elif rsi < 30:
        insights.append("RSI indicates the stock is oversold, potentially signaling a buying opportunity.")
    else:
        insights.append("RSI is neutral, indicating no extreme market conditions.")

    # Moving Averages (Golden Cross/Death Cross)
    if ma50 > ma200:
        insights.append("The 50-day MA is above the 200-day MA, signaling a bullish trend (Golden Cross).")
    elif ma50 < ma200:
        insights.append("The 50-day MA is below the 200-day MA, signaling a bearish trend (Death Cross).")
    else:
        insights.append("The 50-day MA and 200-day MA are equal, indicating market indecision.")

    # Latest Close Price Insight
    insights.append(f"The last closing price is {latest_close:.2f}. Compare with historical prices for resistance/support levels.")

    return insights

def main():
    st.title("Finance Enthusiast")

    if 'fig' not in st.session_state:
        st.session_state.fig = None
    if 'stock_name' not in st.session_state:
        st.session_state.stock_name = None

    with st.sidebar:
        ticker = st.text_input("Enter stock ticker symbol (e.g., AAPL): ").upper()
        start_year = st.number_input("Enter start year:", min_value=1900, max_value=datetime.now().year, step=1, value=datetime.now().year - 5)
        if st.button("Analyze"):
            try:
                start_date_str = f"{start_year}-01-01"
                st.session_state.fig, st.session_state.stock_name = analyze_stock(ticker, start_date_str)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.fig:
        if st.session_state.stock_name:
            st.header(f'{st.session_state.stock_name} ({ticker})')
        st.pyplot(st.session_state.fig, use_container_width=True)

        # Add Interpretation Below the Graph
        insights = interpret_data(pd.read_csv(f'{ticker}.csv'))  # Adjust as needed
        st.subheader("Insights from the Data")
        for insight in insights:
            st.write("- " + insight)

        st.session_state.fig = None
        st.session_state.stock_name = None
