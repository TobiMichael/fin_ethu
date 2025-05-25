import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import yfinance as yf # Import the yfinance library

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Get the Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable in a .env file.")
    st.stop()

# --- Define Tools (Functions for Gemini to call) ---
def get_stock_price(ticker_symbol: str) -> dict:
    """
    Fetches the current stock price and related basic info for a given ticker symbol from Yahoo Finance.
    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., "AAPL", "MSFT", "GOOGL").
    Returns:
        dict: A dictionary containing the stock price, currency, company name, or an error message.
    """
    try:
        if not isinstance(ticker_symbol, str) or not ticker_symbol.strip():
            return {"error": "Invalid ticker symbol provided. Please provide a non-empty string."}

        stock = yf.Ticker(ticker_symbol.upper())
        info = stock.info

        current_price = info.get('currentPrice')
        currency = info.get('currency')
        long_name = info.get('longName', ticker_symbol.upper())

        if current_price is not None and currency is not None:
            return {
                "ticker": ticker_symbol.upper(),
                "companyName": long_name,
                "price": current_price,
                "currency": currency,
                "status": "success"
            }
        else:
            return {"error": f"Could not retrieve price or currency for {ticker_symbol.upper()}. Information might be missing or ticker is invalid.", "status": "error"}
    except Exception as e:
        if "No data found for ticker" in str(e) or "failed to download" in str(e):
             return {"error": f"Could not find data for ticker symbol '{ticker_symbol.upper()}'. It might be invalid.", "status": "error"}
        return {"error": f"An unexpected error occurred while fetching data for {ticker_symbol.upper()}: {e}", "status": "error"}

# Define the tools available to the Gemini model using FunctionDeclaration
tools = [
    genai.FunctionDeclaration(
        name="get_stock_price",
        description="Fetches the current stock price and basic company information for a given ticker symbol from Yahoo Finance.",
        parameters={
            "type": "object",
            "properties": {
                "ticker_symbol": {
                    "type": "string",
                    "description": "The stock ticker symbol (e.g., 'AAPL' for Apple, 'MSFT' for Microsoft)."
                }
            },
            "required": ["ticker_symbol"]
        }
    )
]

# Configure the google.generativeai library with your API key and tools
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model with tools
model = genai.GenerativeModel(
    'gemini-1.5-flash', # Using the gemini-1.5-flash model
    tools=tools, # Pass your defined tools to the model
    tool_config=genai.ToolConfig(
        function_calling=genai.ToolConfig.FunctionCallingConfig(
            mode=genai.ToolConfig.FunctionCallingConfig.Mode.AUTO # Let Gemini decide when to call functions
        )
    )
)

# --- Streamlit App UI ---
st.set_page_config(page_title="Gemini Chatbot with YFinance & Layout", layout="centered")

# --- Main Body ---
st.title("Streamlit Layout Test with Sidebar Chatbot")
st.write("This is a simple layout test to demonstrate Streamlit columns and a chatbot in the sidebar.")

# Divide body into 3 columns
col1, col2, col3 = st.columns(3)

# Place content in each column
with col1:
    st.write("i love you")

with col2:
    st.write("what???")

with col3:
    st.write("I love you dearly")

# --- Chatbot in Sidebar ---
with st.sidebar:
    st.title("🤖 Gemini-Powered Chatbot")
    st.markdown("Ask me anything! I can even fetch **live stock prices** (e.g., 'What is Apple's stock price?', 'Tell me about GOOGL stock').")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I help you today?"})

    # Display previous messages from chat history
    chat_container = st.container(height=400, border=True) # Fixed height for scrollability in sidebar
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Chat Input and Response Logic ---
    if prompt := st.chat_input("What's on your mind?", key="sidebar_chat_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)

        # Prepare chat history for Gemini (includes role and structured parts)
        chat_history_for_gemini = []
        for msg in st.session_state.messages:
            gemini_role = "user" if msg["role"] == "user" else "model"
            content_parts = [{"text": msg["content"]}]
            chat_history_for_gemini.append({"role": gemini_role, "parts": content_parts})

        # Start a chat session with the history
        # Exclude the current user prompt from initial history passed to start_chat
        chat = model.start_chat(history=chat_history_for_gemini[:-1])

        with st.spinner("Thinking..."):
            try:
                response = chat.send_message(prompt)

                gemini_response_text = "I'm sorry, I couldn't get a clear response." # Default message

                if response.candidates:
                    first_candidate = response.candidates[0]
                    
                    # Check if Gemini wants to call a function
                    if first_candidate.function_calls:
                        for function_call in first_candidate.function_calls:
                            function_name = function_call.name
                            function_args = {k: v for k, v in function_call.args.items()}

                            st.info(f"DEBUG: Gemini requested tool: `{function_name}` with args: `{function_args}`")

                            if function_name == "get_stock_price":
                                tool_output = get_stock_price(**function_args)
                                
                                st.info(f"DEBUG: Tool output: {tool_output}")

                                # Send the tool's output back to Gemini
                                tool_response_content = genai.ToolCodeResult(function_name=function_name, stdout=tool_output)
                                
                                # Get the final natural language response from Gemini
                                final_response_from_tool = chat.send_message(tool_response_content)
                                gemini_response_text = final_response_from_tool.text
                            else:
                                gemini_response_text = f"Error: Unknown tool '{function_name}' requested."
                    else:
                        # Gemini returned a text response directly (no function call)
                        gemini_response_text = response.text
                
                # Check for safety feedback even if no candidate was generated
                if response.prompt_feedback and response.prompt_feedback.safety_ratings:
                    # You might want to display safety feedback in a more user-friendly way
                    st.warning(f"Response blocked due to safety concerns: {response.prompt_feedback.safety_ratings}")
                    gemini_response_text = "I'm sorry, I cannot provide a response for that query due to safety guidelines."


                # Add Gemini's final response to chat history
                st.session_state.messages.append({"role": "assistant", "content": gemini_response_text})
                with chat_container.chat_message("assistant"):
                    st.markdown(gemini_response_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.warning("Please try again or check your API key and network connection.")

    # Optional: Clear chat history button
    st.markdown("---") # Separator
    if st.button("Clear Chat", key="clear_chat_button"):
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Chat history cleared. How can I help you now?"})
        st.rerun() # Rerun the app to clear the displayed messages

