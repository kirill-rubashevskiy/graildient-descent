import os
from io import BytesIO

import boto3
import botocore.exceptions
import pandas as pd
import streamlit as st


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ru-central1")  # Default to ru-central1 if not set
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "https://storage.yandexcloud.net")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise EnvironmentError("AWS credentials not found in environment variables.")


@st.cache_data
def load_data_from_s3(bucket_name, s3_key, **params) -> pd.DataFrame:
    """Download a CSV file from S3 and read it into a Pandas DataFrame."""

    # Initialize the S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
    )

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        csv_content = response["Body"].read()
        data = pd.read_csv(BytesIO(csv_content), **params)
        return data
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            st.error(f"Object with key '{s3_key}' not found in bucket '{bucket_name}'.")
        else:
            st.error(f"Failed to load data from S3: {e}")
        raise
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        raise


@st.cache_data
def calculate_quantiles(data: pd.DataFrame, quantiles: list[float]) -> pd.Series:
    """
    Calculate specified quantiles for the 'sold_price' feature in the dataset.

    Parameters:
    data: The dataframe containing the 'sold_price' feature.
    quantiles: A list of quantile values to calculate.

    Returns:
    A series containing the calculated quantile values.

    Raises:
    KeyError if 'sold_price' column is not found in the dataframe.
    """
    if "sold_price" not in data.columns:
        raise KeyError("'sold_price' column not found in the data.")
    return data["sold_price"].quantile(quantiles)


@st.cache_data
def get_unique_values(data: pd.DataFrame, features: list[str]) -> dict:
    """
    Get unique values for specified categorical features in the dataset.

    Parameters:
    data: The dataframe containing the categorical features.
    features: A list of feature names for which to retrieve unique values.

    Returns:
    A dictionary where keys are feature names and values are arrays of unique values.

    Raises:
    KeyError if any of the specified features are not found in the dataframe.
    """
    missing_features = [feature for feature in features if feature not in data.columns]
    if missing_features:
        raise KeyError(
            f"The following features were not found in the data: {missing_features}. Please check that the feature names are correct."
        )

    return {feature: data[feature].unique() for feature in features}
