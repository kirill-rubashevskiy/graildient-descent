import os

import boto3
import pandas as pd
import pytest
from moto import mock_aws


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """
    Sample data fixture to be used across multiple tests.
    """
    return pd.DataFrame(
        {
            "n_photos": [1, 3, 2, 4, 5],
            "designer": ["Gucci", "Prada", "Louis Vuitton", "Chanel", "Hermès"],
            "condition": ["New", "Gently Used", "Used", "Worn", "New"],
            "color": ["Red", "Blue", "Green", "Black", "White"],
            "department": [
                "menswear",
                "menswear",
                "womenswear",
                "womenswear",
                "womenswear",
            ],
            "category": ["tops", "bottoms", "dresses", "accessories", "footwear"],
            "subcategory": ["cardigans", "jeans", "midi-dresses", "belts", "boots"],
            "size": ["S", "28", "XS", "ONE SIZE", "8"],
            "item_name": ["Shirt", "Jacket", "Shoes", "Hat", "Necklace"],
            "description": [
                "Red cotton shirt",
                "Blue denim jacket",
                "Black leather shoes",
                "Cowboy hat.",
                "Silver necklace.",
            ],
            "hashtags": [
                "fashion style",
                "none",
                "leather shoes",
                "rodeo cowboy",
                "jewelry",
            ],
        }
    )


@pytest.fixture
def sample_targets() -> pd.Series:
    """
    Sample target data for Model testing.
    """
    return pd.Series([100, 200, 150, 300, 400])


@pytest.fixture(scope="function")
def aws_credentials():
    """
    Mocked Yandex Cloud S3 Credentials for moto.
    """
    os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = "https://storage.yandexcloud.net"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    """
    Provide a mocked S3 client using moto for testing S3 interactions.
    """
    with mock_aws():
        yield boto3.client(
            "s3",
            region_name="ru-central1",
            endpoint_url="https://storage.yandexcloud.net",
        )


@pytest.fixture
def create_bucket(s3):
    """
    Fixture to create an S3 bucket with a specific location constraint.
    """
    location = {"LocationConstraint": "ru-central1"}
    bucket_name = "my-bucket"
    s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
