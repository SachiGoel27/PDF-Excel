import streamlit as st
import sennebogen as sennebogen
import qbo as qbo


dark_yellow_css = """
<style>
body {
    background-color: #333300; 
    color: #FFD700; 
}

subheader {
    color: white;
}

h1, h2, h3, h4, h5, h6 {
    color: #FFCC00; 
}

.stButton>button {
    background-color: #FFD700;
    color: black;
    border-radius: 5px;
    border: 1px solid #FFCC00;
    font-size: 16px;
    font-weight: bold;
}

.stButton>button:hover {
    background-color: #FFCC33; 
    color: #333300;
}


.stSidebar {
    background-color: #4D4D00; 
    color: #FFD700;
}

.stSidebar .css-1v3fvcr {
    color: #FFD700; 
}

input, textarea {
    background-color: #4D4D00; 
    color: #FFD700;
    border: 1px solid #FFCC00;
    border-radius: 5px;
}

a, .css-1fv8s86, .css-1hxh2wk, .css-1ynw3xd {
    color: #FFD700; 
}
</style>
"""
st.markdown(dark_yellow_css, unsafe_allow_html=True)

st.title('File Conversions')
st.subheader("Input in your Sennebogen file to turn into an Excel file.", divider="gray")
file = st.file_uploader("Input a PDF file", type=["PDF"], key="2")
if st.button("Process File", key="2b"):
    if file is not None:
        with st.spinner("Processing..."):
            excel_data = sennebogen.extract_tables_(file)

            if excel_data:
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=f"{file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No tables found in the PDF.")
    else:
        st.warning("Please upload a file before submitting.")

st.subheader("Input in your QBO file to turn into a Receving Report file.", divider="gray")
file = st.file_uploader("Input a PDF file", type=["PDF"], key="4")
if st.button("Process File", key="4b"):
    if file is not None:
        with st.spinner("Processing..."):
            qbo_data = qbo.extract_values(file)
            if qbo_data:
                st.download_button(
                    label="Download PDF File",
                    data=qbo_data,
                    file_name=f"{file.name}RecevingReport.pdf",
                )
            else:
                st.error("No tables found in the PDF.")
    else:
        st.warning("Please upload a file before submitting.")


st.text("Below is a work in progress...")
st.subheader("Input in your Liebherr file to turn into an Excel file.", divider="gray")
file = st.file_uploader("Input a PDF file", type=["PDF"], key="3")

if st.button("Process File", key="3b"):
    if file is not None:
        with st.spinner("Processing..."):
            excel_data = sennebogen.extract_tables_(file)

            if excel_data:
                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=f"{file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("No tables found in the PDF.")
    else:
        st.warning("Please upload a file before submitting.")
