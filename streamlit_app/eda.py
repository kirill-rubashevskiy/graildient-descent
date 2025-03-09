import streamlit as st
from modules.data_utils import calculate_quantiles, load_data_from_s3
from modules.eda_image_features import display_image_features
from modules.eda_tabular_features.categorical_features import (
    display_categorical_features,
)
from modules.eda_tabular_features.numerical_features import display_numerical_features
from modules.eda_text_features import display_text_features


data = load_data_from_s3("data/raw/sold_listings.csv", nrows=10000)
text_stats = load_data_from_s3("data/preprocessed/preprocessed_text_stats_10k.csv")
text_tokens = text_ngrams = load_data_from_s3(
    "data/preprocessed/token_intersection_long_10k.csv"
)
text_ngrams = load_data_from_s3("data/preprocessed/preprocessed_text_ngrams_10k.csv")
text_sentiment = load_data_from_s3(
    "data/preprocessed/preprocessed_text_sentiment_10k.csv"
)
q_low, q_high = calculate_quantiles(data, [0.25, 0.75])

st.title("Exploratory Data Analysis")

st.write(
    """
We’ve collected data on 10,000 sold listings, so it's time to dive into the analysis.
"""
)

tab1, tab2, tab3 = st.tabs(["Tabular Features", "Text Features", "Image Features"])


with tab1:  # Tabular Features

    display_numerical_features(data)
    display_categorical_features(data, q_low, q_high)

with tab2:  # Text Features

    display_text_features(
        data, text_stats, text_tokens, text_ngrams, text_sentiment, q_low, q_high
    )

with tab3:  # Image Features

    display_image_features()
