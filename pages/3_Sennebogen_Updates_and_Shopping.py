import streamlit as st
import senn_web

st.title("Sennebogen Item Update and Shopping for Items")
st.markdown("""
Here you can either get information from the Sennebogen 
webiste given some items or you can add all such items to the Sennebogen shopping cart.
""")

st.subheader("Necessary Credentials")
st.markdown("To prevent senstive information apperaing on GitHub please fill in the user name and password for the Sennebogen website.")

username = st.text_input("Username", placeholder="Enter your username").strip()

password = st.text_input("Password", type="password", placeholder="Enter your password").strip()

if st.button("Log"):
    if not(username and password):
        st.error("Please enter both username and password")
    # check the credintationals
    elif senn_web.check_cred(username, password):
        st.success("Credentials are correct.")
    else:
        st.error("Credentials are incorrect.")

st.subheader("Item Updates")
st.markdown("This is not ready yet.")
file = st.file_uploader("Input an Excel file", type=["xlsx", "xls"], key="process")
if st.button("Process File", key="process1"):
    if file is not None:
        pass
        # add logic below
        # with st.spinner("Processing..."):
        #     excel_data = sennebogen.extract_tables_(file, 1)

        #     if excel_data:
        #         st.download_button(
        #             label="Download Excel File",
        #             data=excel_data,
        #             file_name=f"{file.name}.xlsx",
        #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        #         )
        #     else:
        #         st.error("No tables found in the PDF.")
    else:
        st.warning("Please upload a file before submitting.")

st.subheader("Add to Shopping Cart")
file = st.file_uploader("Input an Excel file", type=["xlsx", "xls"], key="buy")

if st.button("Process File", key="buy1"):
    if file is not None and username and password:
        with st.spinner("Processing..."):
            result = senn_web.add_to_cart(file, username, password)
            
            if result:
                st.success("Processing completed!")
                
                # Display results
                for item, status in result.items():
                    if "not found" in status.lower():
                        st.error(f"Item {item}: {status}")
                    elif "not enough stock" in status.lower():
                        st.warning(f"Item {item}: {status}")
                    else:
                        st.warning(f"Item {item}: {status}")
            else:
                st.error("Failed to process the file.")
    else:
        st.warning("Please upload a file and enter username/password before submitting.")