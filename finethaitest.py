import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import yfinance as yf # Import yfinance library

# --- Configuration ---
# Load environment variables from a .env file (recommended for API keys)
# Make sure you have a .env file in the same directory as app.py with:
# GEMINI_API_KEY="YOUR_API_KEY_HERE"
load_dotenv()

# Get the Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable in a .env file.")
    st.stop() # Stop the app if the key is missing

# Configure the google.generativeai library with your API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model
# CHANGED: Now using 'gemini-1.5-flash'
# This model is optimized for speed and efficiency, suitable for high-volume, low-latency tasks.
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Streamlit App UI ---
# Set page configuration at the very beginning
st.set_page_config(page_title="Gemini Chatbot with Layout", layout="centered")

# --- Session State Initialization ---
# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I help you today?"})

# Initialize stock data in session state
if "stock_data" not in st.session_state:
    st.session_state.stock_data = None
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = ""

# --- Main Body ---
st.title("Streamlit Layout Test with Sidebar")
st.write("This is a simple layout test to demonstrate Streamlit columns and a sidebar.")

# Divide body into 3 columns
col1, col2, col3 = st.columns(3)

# Place content in each column
with col1:
    st.write("i love you")

with col2:
    st.write("what???")

with col3:
    st.write("I love you dearly")

st.markdown("---") # Separator

# --- Stock Data Fetcher Section ---
st.header("📈 Stock Data Fetcher")
st.write("Enter a stock ticker symbol (e.g., AAPL, GOOGL) to fetch its historical data.")

ticker_input = st.text_input("Enter Ticker Symbol", value=st.session_state.current_ticker, key="ticker_symbol_input")

if st.button("Fetch Stock Data", key="fetch_stock_data_button"):
    if ticker_input:
        st.session_state.current_ticker = ticker_input.upper()
        try:
            # Fetch historical data for the last 30 days
            ticker = yf.Ticker(st.session_state.current_ticker)
            hist = ticker.history(period="30d")
            if not hist.empty:
                st.session_state.stock_data = hist
                st.success(f"Successfully fetched data for {st.session_state.current_ticker}!")
                st.dataframe(hist.tail()) # Display last few rows
            else:
                st.session_state.stock_data = None
                st.warning(f"No historical data found for {st.session_state.current_ticker}. Please check the ticker symbol.")
        except Exception as e:
            st.session_state.stock_data = None
            st.error(f"Error fetching data for {st.session_state.current_ticker}: {e}")
    else:
        st.warning("Please enter a ticker symbol.")

# Display fetched stock data if available
if st.session_state.stock_data is not None:
    st.subheader(f"Historical Data for {st.session_state.current_ticker}")
    st.dataframe(st.session_state.stock_data)

st.markdown("---") # Separator

# --- Chatbot in Sidebar ---
# Streamlit only supports one sidebar, which is on the left
with st.sidebar:
    st.title("🤖 Gemini-Powered Chatbot")
    st.markdown("Ask me anything! I'm powered by Google's Gemini AI. This simple bot remembers your current conversation.")
    st.markdown("If you've fetched stock data, I can answer questions about it!")

    # Display previous messages from chat history
    # Use a container to make the chat messages scrollable if they get too long
    chat_container = st.container(height=400, border=True) # Fixed height for scrollability in sidebar
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Chat Input and Response Logic ---
    # Get user input from the chat input box
    # Using a unique key for the chat input in the sidebar
    if prompt := st.chat_input("What's on your mind?", key="sidebar_chat_input"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"): # Display in the chat container
            st.markdown(prompt)

        # Prepare context from stock data if available
        stock_context = ""
        if st.session_state.stock_data is not None:
            # Convert the last few rows of stock data to a string for context
            stock_summary = st.session_state.stock_data.tail(5).to_string()
            stock_context = f"\n\nHere is recent historical stock data for {st.session_state.current_ticker}:\n{stock_summary}\n\n"
            st.info(f"Using stock data for {st.session_state.current_ticker} as context.")

        # Generate response from Gemini
        with st.spinner("Thinking..."): # Show a spinner while waiting for AI response
            try:
                # The Gemini models can handle chat, but their 'history' expectation
                # can sometimes be slightly different for text-only turns.
                # It's generally safest to explicitly send parts with 'text' key.
                chat_history_for_gemini = []
                for msg in st.session_state.messages:
                    gemini_role = "user" if msg["role"] == "user" else "model"
                    chat_history_for_gemini.append({"role": gemini_role, "parts": [{"text": msg["content"]}]})

                # Prepend stock context to the current user prompt if available
                current_prompt_with_context = stock_context + prompt

                # Start a chat session with the history
                # Exclude the current user prompt (which now includes context) from initial history passed to start_chat
                # as it will be sent separately by chat.send_message()
                chat = model.start_chat(history=chat_history_for_gemini[:-1])

                # Send the current user prompt with context
                response = chat.send_message(current_prompt_with_context)

                # Access the text from the response
                gemini_response_text = response.text

                # Add Gemini's response to chat history
                st.session_state.messages.append({"role": "assistant", "content": gemini_response_text})
                with chat_container.chat_message("assistant"): # Display in the chat container
                    st.markdown(gemini_response_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.warning("Please try again or check your API key and network connection.")

    # Optional: Clear chat history button
    st.markdown("---") # Separator
    # Using a unique key for the clear chat button in the sidebar
    if st.button("Clear Chat", key="clear_chat_button"):
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Chat history cleared. How can I help you now?"})
        st.session_state.stock_data = None # Also clear stock data
        st.session_state.current_ticker = "" # Also clear current ticker
        st.rerun() # Rerun the app to clear the displayed messages
