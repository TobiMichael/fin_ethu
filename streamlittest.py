import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

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
# 'gemini-pro' is suitable for text-based chat.
# For multimodal (text + image), you might use 'gemini-pro-vision'.
model = genai.GenerativeModel('gemini-pro')

# --- Streamlit App UI ---
# Set page configuration at the very beginning
st.set_page_config(page_title="Gemini Chatbot with Layout", layout="centered")

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

# --- Chatbot in Sidebar ---
# Streamlit only supports one sidebar, which is on the left
with st.sidebar:
    st.title("🤖 Gemini-Powered Chatbot")
    st.markdown("Ask me anything! I'm powered by Google's Gemini AI. This simple bot remembers your current conversation.")

    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "Hello! How can I help you today?"})

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

        # Generate response from Gemini
        with st.spinner("Thinking..."): # Show a spinner while waiting for AI response
            try:
                # Convert st.session_state.messages into a format suitable for start_chat
                chat_history_for_gemini = []
                for msg in st.session_state.messages:
                    gemini_role = "user" if msg["role"] == "user" else "model"
                    chat_history_for_gemini.append({"role": gemini_role, "parts": [msg["content"]]})

                # Start a chat session with the history
                # Exclude the current user prompt from initial history passed to start_chat
                # as it will be sent separately by chat.send_message()
                chat = model.start_chat(history=chat_history_for_gemini[:-1])

                # Send the current user prompt
                response = chat.send_message(prompt)

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
        st.rerun() # Rerun the app to clear the displayed messages
