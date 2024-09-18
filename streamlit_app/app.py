import streamlit as st


intro = st.Page("intro.py", title="Intro", default=True)
data_collection = st.Page("data_collection.py", title="Data Collection")
eda = st.Page("eda.py", title="Exploratory Data Analysis")

# Sidebar navigation
page = st.navigation([intro, data_collection, eda])

# Set up the page configuration
st.set_page_config(page_title="Graildient Descent")

page.run()
