import streamlit as st

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

# --- Left Sidebar ---
# Streamlit only supports one sidebar, which is on the left
with st.sidebar:
    st.write("input sidebar")
    # You can add more elements here, e.g.,
    # st.button("Click me")
    # st.slider("Select a value", 0, 100)

# --- Regarding a Right Sidebar ---
# Streamlit does NOT have a built-in right sidebar feature like st.sidebar.
# Achieving a panel on the right requires different layout techniques
# using columns or containers in the main body, but it won't behave
# like a collapsible sidebar.
# For the purpose of this script, we will only use the standard left sidebar.
