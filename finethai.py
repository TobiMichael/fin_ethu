import streamlit as st
import google.generativeai as genai
import yfinance as yf
import json # For handling tool output
import pandas as pd # For displaying historical data nicely

# --- Configuration ---
# Load Gemini API key from Streamlit secrets
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=gemini_api_key)
except KeyError:
    st.error("Gemini API key not found. Please add it to your Streamlit secrets.toml file.")
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
    
