import streamlit as st
from database.db_connect import get_session
from components.data_deposit import show_data_deposit_section
from components.data_analysis import show_data_analysis_section

# Set page configuration
st.set_page_config(page_title="Immune Atlas Demo", layout="wide")

# Title and Introduction
st.title("Welcome to the Immune Atlas")
st.write("""
The Immune Atlas aggregates and analyzes cytometry datasets to accelerate drug development by identifying optimal cancer types and patient subsets. Explore how you can contribute data or leverage our insights below.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
section = st.sidebar.radio("Choose an Action:", ["I am depositing data", "I am looking at data"])

# Initialize DB session
db_session = get_session()

# Display the appropriate section
if section == "I am depositing data":
    show_data_deposit_section(db_session)
else:
    show_data_analysis_section(db_session)

# Close the session
db_session.close()

# Footer
st.write("---")
st.write("Contact us to learn more or start contributing: info@teiko.bio")