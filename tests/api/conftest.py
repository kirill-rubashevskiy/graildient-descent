from unittest.mock import create_autospec

import numpy as np
import pytest

from api.services import PredictionService
from data_collection.scraper import GrailedListingScraper


# Shared test constants
VALID_LISTING_DATA = {
    "designer": "nike",
    "department": "menswear",
    "category": "footwear",
    "subcategory": "low-top-sneakers",
    "n_photos": 5,
    "item_name": "Air Force 1",
    "size": "10",
    "color": "white",
    "condition": "Used",
    "description": "Classic sneaker in good condition",
    "hashtags": "sneakers nike airforce1",
}

VALID_URL = "https://www.grailed.com/listings/12345"


@pytest.fixture
def mock_model():
    class MockModel:
        def predict(self, X):
            # Always return a prediction of 100.0 for testing
            return np.array([100.0])

        @property
        def model_name(self):
            return "mock_model"

        @property
        def estimator_class(self):
            return "lr"

        @property
        def use_tab_features(self):
            return True

        @property
        def use_text_features(self):
            return False

    return MockModel()


@pytest.fixture
def mock_scraper():
    scraper = create_autospec(GrailedListingScraper)
    scraper.get_listing_data.return_value = VALID_LISTING_DATA
    return scraper


@pytest.fixture
def mock_metrics():
    return {"rmsle": 0.5, "wape": 0.3}


@pytest.fixture
def prediction_service(mock_model, mock_metrics, mock_scraper):
    return PredictionService(mock_model, mock_metrics, mock_scraper)
