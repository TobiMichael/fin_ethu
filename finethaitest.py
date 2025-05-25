import streamlit as st
import google.generativeai as genai
import yfinance as yf
import json # For handling tool output
import pandas as pd # For displaying historical data nicely
import os # For environment variables
from dotenv import load_dotenv # Import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Load Gemini API key from environment variables
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=gemini_api_key)
except ValueError as e:
    st.error(f"Configuration error: {e}. Please ensure GEMINI_API_KEY is set in your .env file.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during API key configuration: {e}")
    st.stop()


# Initialize the Gemini model with tools
# We'll define the tools that Gemini can use to interact with yfinance
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[
        genai.Tool(
            function_declarations=[
                genai.FunctionDeclaration(
                    name="get_stock_price",
                    description="Get the current stock price for a given ticker symbol.",
                    parameters=genai.FunctionParameters(
                        type=genai.Type.OBJECT,
                        properties={
                            "ticker_symbol": genai.Schema(type=genai.Type.STRING, description="The stock ticker symbol (e.g., 'AAPL', 'GOOGL').")
                        },
                        required=["ticker_symbol"],
                    ),
                ),
                genai.FunctionDeclaration(
                    name="get_company_info",
                    description="Get general information about a company for a given ticker symbol.",
                    parameters=genai.FunctionParameters(
                        type=genai.Type.OBJECT,
                        properties={
                            "ticker_symbol": genai.Schema(type=genai.Type.STRING, description="The stock ticker symbol (e.g., 'AAPL', 'GOOGL').")
                        },
                        required=["ticker_symbol"],
                    ),
                ),
                genai.FunctionDeclaration(
                    name="get_historical_data",
                    description="Get historical stock data (Open, High, Low, Close, Volume) for a given ticker symbol and period.",
                    parameters=genai.FunctionParameters(
                        type=genai.Type.OBJECT,
                        properties={
                            "ticker_symbol": genai.Schema(type=genai.Type.STRING, description="The stock ticker symbol (e.g., 'AAPL', 'GOOGL')."),
                            "period": genai.Schema(type=genai.Type.STRING, description="The period for historical data (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'). Defaults to '1mo' if not specified."),
                            "interval": genai.Schema(type=genai.Type.STRING, description="The interval for historical data (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'). Defaults to '1d' for periods > 7d, '1h' for periods <= 7d. Note: '1m' interval only available for last 7 days."),
                        },
                        required=["ticker_symbol"],
                    ),
                ),
            ]
        )
    ]
)

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Start a new chat session with the model
    st.session_state.chat = model.start_chat(history=[])

# --- yfinance Tool Functions ---
def get_stock_price(ticker_symbol: str) -> str:
    """Fetches the current stock price for a given ticker symbol."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        todays_data = ticker.history(period='1d')
        if not todays_data.empty:
            current_price = todays_data['Close'].iloc[-1]
            return json.dumps({"ticker": ticker_symbol, "current_price": f"{current_price:.2f}"})
        else:
            return json.dumps({"error": f"Could not retrieve current price for {ticker_symbol}. It might be an invalid ticker or market is closed."})
    except Exception as e:
        return json.dumps({"error": f"An error occurred while fetching price for {ticker_symbol}: {str(e)}"})

def get_company_info(ticker_symbol: str) -> str:
    """Fetches general company information for a given ticker symbol."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        # Extract some key information
        relevant_info = {
            "shortName": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "fullTimeEmployees": info.get("fullTimeEmployees"),
            "website": info.get("website"),
            "longBusinessSummary": info.get("longBusinessSummary")
        }
        return json.dumps(relevant_info)
    except Exception as e:
        return json.dumps({"error": f"An error occurred while fetching info for {ticker_symbol}: {str(e)}"})

def get_historical_data(ticker_symbol: str, period: str = '1mo', interval: str = '1d') -> str:
    """Fetches historical stock data for a given ticker symbol, period, and interval."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        if not hist.empty:
            # Convert DataFrame to a list of dictionaries for JSON serialization
            hist_data = hist.reset_index().to_dict(orient='records')
            # Format Date column for better readability if it's a datetime object
            for record in hist_data:
                if 'Date' in record and isinstance(record['Date'], pd.Timestamp):
                    record['Date'] = record['Date'].strftime('%Y-%m-%d %H:%M:%S') # Or just '%Y-%m-%d'
            return json.dumps({"ticker": ticker_symbol, "period": period, "interval": interval, "data": hist_data})
        else:
            return json.dumps({"error": f"No historical data found for {ticker_symbol} with period {period} and interval {interval}. Check ticker or parameters."})
    except Exception as e:
        return json.dumps({"error": f"An error occurred while fetching historical data for {ticker_symbol}: {str(e)}"})

# Map tool names to actual functions
tool_functions = {
    "get_stock_price": get_stock_price,
    "get_company_info": get_company_info,
    "get_historical_data": get_historical_data,
}

# --- Streamlit UI ---
st.set_page_config(page_title="Gemini Stock Chatbot", layout="wide")

st.title("📈 Gemini Stock Chatbot")
st.markdown("Ask me about stock prices, company info, or historical data!")

# Main chat display area
chat_display_area = st.container()

with chat_display_area:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["parts"][0]["text"])
        elif message["role"] == "model":
            # Check if the model's response contains tool calls or tool outputs
            if any(part.function_call for part in message["parts"]):
                # This is a tool call/response, which we'll handle internally,
                # but we can show a brief message that a tool was used.
                # For simplicity, we'll just show the final text response from Gemini.
                # The actual tool execution and response are handled in the background.
                pass # We only want to display the final text response from the model
            elif any(part.function_response for part in message["parts"]):
                pass # Don't display raw tool responses, only the model's summary
            else:
                st.chat_message("assistant").write(message["parts"][0]["text"])

# Chat input in the sidebar
with st.sidebar:
    st.header("Chat with Gemini")
    user_input = st.chat_input("Enter your query:", key="chat_input", on_submit=None) # on_submit=None to allow manual submit

    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
        st.chat_message("user").write(user_input)

        with st.spinner("Thinking..."):
            try:
                # Send user message to Gemini
                response = st.session_state.chat.send_message(user_input)

                # Process potential tool calls
                tool_responses = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        args = {key: value for key, value in function_call.args.items()}

                        st.info(f"Gemini wants to call tool: `{function_name}` with arguments: `{args}`")

                        if function_name in tool_functions:
                            # Execute the tool function
                            tool_output = tool_functions[function_name](**args)
                            tool_responses.append(tool_output)
                            st.session_state.chat_history.append(
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response=json.loads(tool_output) # Ensure response is a dict/JSON object
                                    )
                                )
                            )
                        else:
                            error_msg = f"Error: Tool '{function_name}' not found."
                            tool_responses.append(json.dumps({"error": error_msg}))
                            st.session_state.chat_history.append(
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"error": error_msg}
                                    )
                                )
                            )

                # If there were tool responses, send them back to Gemini for a final text response
                if tool_responses:
                    # Append the tool responses to the chat history, then send to model again
                    # The `send_message` method automatically handles adding the response to history
                    # and sending tool outputs back to the model.
                    final_response = st.session_state.chat.send_message(tool_responses)
                    model_response_text = final_response.text
                else:
                    # If no tool calls, just get the text directly
                    model_response_text = response.text

                # Add model's final text response to chat history and display
                st.session_state.chat_history.append({"role": "model", "parts": [{"text": model_response_text}]})
                st.chat_message("assistant").write(model_response_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.chat_history.append({"role": "model", "parts": [{"text": f"Sorry, I encountered an error: {e}"}]})
                st.chat_message("assistant").write(f"Sorry, I encountered an error: {e}")

        # Rerun to update the chat display
        st.experimental_rerun()

st.sidebar.markdown("""
---
**How to use:**
1.  **Create a `.env` file** in the same directory as this script and add `GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"`.
2.  Ask questions like:
    * "What is the price of GOOGL?"
    * "Tell me about Apple."
    * "Show me the historical data for MSFT for the last 6 months."
    * "What was Amazon's price in 2023?" (Note: For specific dates, Gemini might need more context or you might need to refine the prompt.)
""")
