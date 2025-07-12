# pages/1_Sortly_Price_Updater.py

import streamlit as st
import pandas as pd
import io
# Make sure sortly_backend.py is in the main project folder
from sortly_backend import run_update_process

# --- Page Configuration ---
st.set_page_config(
    page_title="Sortly Price Updater",
    layout="wide"
)

# --- Add your custom CSS for a consistent look ---
dark_yellow_css = """
<style>
body {
    background-color: #333300; 
    color: #FFD700; 
}
h1, h2, h3, h4, h5, h6, .st-emotion-cache-1629p8f e1nzilvr2, .st-emotion-cache-10trblm e1nzilvr1 {
    color: #FFCC00; 
}
.stButton>button {
    background-color: #FFD700; color: black; border-radius: 5px;
    border: 1px solid #FFCC00; font-size: 16px; font-weight: bold;
}
.stButton>button:hover { background-color: #FFCC33; color: #333300; }
input, textarea {
    background-color: #4D4D00; color: #FFD700;
    border: 1px solid #FFCC00; border-radius: 5px;
}
</style>
"""
st.markdown(dark_yellow_css, unsafe_allow_html=True)

# --- App Header ---
st.title("Sortly Price Updater Tool")
st.markdown("""
This tool allows you to bulk update item prices in your Sortly inventory.
**Instructions:**
1.  **Download the Example Format** to see the required Excel structure.
2.  **Fill your Excel file** with the `Stock #` and new `Value` for each item.
3.  **Drag and drop** your completed Excel file into the uploader below.
4.  Click the **"Start Update Process"** button and monitor the live log.
""")

# --- API Key Check ---
try:
    api_token = st.secrets["SORTLY_API_TOKEN"]
except (KeyError, FileNotFoundError):
    st.error("🚨 **Error:** SORTLY_API_TOKEN not found in `.streamlit/secrets.toml`!")
    st.stop()

# --- Example File Download ---
with open("path/to/your/template.xlsx", "rb") as file:
    excel_data = file.read()

st.download_button(
    label="⬇️ Download Example Format",
    data= excel_data,
    file_name="example_format.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- File Uploader ---
st.markdown("---")
uploaded_file = st.file_uploader(
    "📂 Drag and Drop Your Excel File Here",
    type=["xlsx"]
)

# --- Main Logic ---
if uploaded_file is not None:
    if st.button("🚀 Start Update Process"):
        st.session_state.log_messages = []
        st.session_state.log_counter = 0

        log_container = st.container()
        log_container.write("--- Live Log ---")
        log_placeholder = log_container.empty()

        def streamlit_output_callback(message):
            st.session_state.log_messages.append(str(message))

            # Update text
            log_placeholder.markdown(
                f"""
                <div style="height:400px; overflow-y:scroll; background-color:#1e1e1e; color:#FFD700;
                            border:1px solid #FFCC00; border-radius:5px; padding:10px; font-family:monospace;" 
                     id="log-box">
                    {"<br>".join(st.session_state.log_messages)}
                </div>
                <script>
                    var logBox = document.getElementById('log-box');
                    logBox.scrollTop = logBox.scrollHeight;
                </script>
                """,
                unsafe_allow_html=True
            )

            st.session_state.log_counter += 1

        with st.spinner("Processing... This may take several minutes."):
            run_update_process(
                api_token=api_token,
                uploaded_file=uploaded_file,
                output_callback=streamlit_output_callback
            )

        st.success("✅ Process Finished!")