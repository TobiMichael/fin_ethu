import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Gemini API key not found. Please set the GEMINI_API_KEY environment variable in a .env file.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

st.title("Gemini Model Availability Check")
st.write("Checking which Gemini models are available with your API key...")

try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)

    if available_models:
        st.success("Successfully retrieved available models!")
        st.write("Models available for `generateContent` (text generation):")
        for model_name in available_models:
            st.write(f"- `{model_name}`")

        if 'models/gemini-1.0-pro' in available_models:
            st.info("Great! `models/gemini-1.0-pro` is listed as available.")
        else:
            st.warning("`models/gemini-1.0-pro` is NOT listed as available with your current API key.")
            st.info("Please generate a new API key from Google AI Studio, or try a model that is listed as available.")
    else:
        st.warning("No models supporting `generateContent` were found with your API key.")
        st.info("This indicates an issue with your API key or project permissions. Please ensure the Gemini API is enabled for your project and your API key is correct.")

except Exception as e:
    st.error(f"An error occurred while listing models: {e}")
    st.error("Please double-check your `GEMINI_API_KEY` in the `.env` file and ensure it's correct.")
    st.info("You can get a new key from: https://aistudio.google.com/app/apikey")
