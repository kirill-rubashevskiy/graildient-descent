import streamlit as st
from modules.data_collection_scraper import display_data_collection_scraper


st.markdown(
    """
    # Data Collection

    First things first — let’s gather some data!
    """
)

display_data_collection_scraper()
