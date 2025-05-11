import streamlit as st

# 1. Title
st.title("Streamlit Layout Test")

# 2. Description
st.write("This is a simple layout test to demonstrate Streamlit columns.")

# 3. Divide body into 3 columns
col1, col2, col3 = st.columns(3)

# Place content in each column
with col1:
    st.write("i love you")

with col2:
    st.write("what???")

with col3:
    st.write("I love you dearly")
