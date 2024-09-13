import os
import random
from io import StringIO

import boto3
import numpy as np
import pandas as pd
from mergedeep import merge


def load_data(
    filename: str, from_s3: bool = False, bucket_name: str = None, **params
) -> pd.DataFrame:
    """
    Load a CSV dataset by name from the data/ folder, its subfolders, or an S3 bucket.

    Parameters:
        filename: The name of the CSV file to load (including extension).
        from_s3: Whether to load the file from an S3 bucket.
        bucket_name: The name of the S3 bucket (required if from_s3 is True).
        **params: Additional parameters to pass to the pd.read_csv function.

    Returns:
        The loaded dataset as a Pandas DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist in the data/ directory, its subfolders, or the S3 bucket.
        ValueError: If from_s3 is True but no bucket_name is provided.
        EnvironmentError: If required environment variables for S3 access are not set.
    """
    if from_s3:
        # Fetch Yandex S3 credentials from environment variables
        YC_ACCESS_KEY_ID = os.getenv("YC_ACCESS_KEY_ID")
        YC_SECRET_ACCESS_KEY = os.getenv("YC_SECRET_ACCESS_KEY")
        YC_REGION = os.getenv("YC_REGION", "ru-central1")  # Default region
        YC_ENDPOINT_URL = os.getenv(
            "YC_ENDPOINT_URL", "https://storage.yandexcloud.net"
        )

        if not YC_ACCESS_KEY_ID or not YC_SECRET_ACCESS_KEY:
            raise EnvironmentError(
                "Yandex Cloud credentials not found in environment variables."
            )

        if not bucket_name:
            raise ValueError("Bucket name must be provided when using S3.")

        # Load the CSV file from Yandex S3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=YC_ACCESS_KEY_ID,
            aws_secret_access_key=YC_SECRET_ACCESS_KEY,
            region_name=YC_REGION,
            endpoint_url=YC_ENDPOINT_URL,
        )
        try:
            obj = s3.get_object(Bucket=bucket_name, Key=filename)
            df = pd.read_csv(StringIO(obj["Body"].read().decode("utf-8")), **params)
        except s3.exceptions.NoSuchKey:
            raise FileNotFoundError(
                f"The file {filename} was not found in the S3 bucket {bucket_name}."
            )
    else:
        # Search for the file in the data/ folder and its subfolders
        for root, _dirs, files in os.walk("data/"):
            if filename in files:
                data_path = os.path.join(root, filename)
                break
        else:
            raise FileNotFoundError(
                f"The file {filename} was not found in the data/ directory or its subfolders."
            )

        # Load the CSV file into a DataFrame
        df = pd.read_csv(data_path, **params)

    return df


def set_random_seed(seed: int = 42):
    """
    Set the random seed for reproducibility across the entire experiment.

    Parameters:
        seed: The seed value to use for all random components.
    """
    random.seed(seed)
    np.random.seed(seed)
    return seed


def unflatten(flat_dict: dict) -> dict:
    """
    Converts a flat dictionary with dotted keys into a nested dictionary.

    Parameters:
        flat_dict: A flat dictionary where keys may contain dots ('.') to represent nested levels.

    Returns:
        dict: A nested dictionary constructed by expanding the dotted keys into nested dictionaries.
    """

    def dotsplit(key: str, value):
        keys = key.split(".")
        if len(keys) == 1:
            return {key: value}
        # Recursively create the nested structure
        return {keys[0]: dotsplit(".".join(keys[1:]), value)}

    unflattened = {}
    for k, v in flat_dict.items():
        merge(unflattened, dotsplit(k, v))

    return unflattened
