import streamlit as st


intro = st.Page("intro.py", title="Intro", default=True)
eda = st.Page("eda.py", title="Exploratory Data Analysis")

# Sidebar navigation
page = st.navigation([intro, eda])

# Set up the page configuration
st.set_page_config(page_title="Graildient Descent")

page.run()
