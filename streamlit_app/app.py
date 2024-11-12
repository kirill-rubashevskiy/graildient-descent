import streamlit as st


intro = st.Page("intro.py", title="Intro", default=True)
data_collection = st.Page("data_collection.py", title="Data Collection")
eda = st.Page("eda.py", title="Exploratory Data Analysis")
ml_experiments = st.Page("ml_experiments.py", title="ML Experiments")

# Sidebar navigation
page = st.navigation([intro, data_collection, eda, ml_experiments])

# Set up the page configuration
st.set_page_config(page_title="Graildient Descent")

page.run()
