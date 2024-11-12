import streamlit as st
from modules.ml_experiments_setup import display_ml_experiments_setup


st.title("ML Experiments")

st.write(
    """
    Now after we collected enough data and explored it, it's time for ML experiments.
    """
)

tab1, tab2 = st.tabs(["Experiments Setup", "Experiments Results"])

with tab1:  # Experiments Setup

    display_ml_experiments_setup()
