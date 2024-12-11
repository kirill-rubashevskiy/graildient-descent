import pytest
from fastapi import HTTPException

from tests.api.conftest import VALID_LISTING_DATA, VALID_URL


MOCK_PROCESSED_TEXT = "processed text"


def test_predict_from_url_success(prediction_service):
    """Test successful prediction from URL"""
    prediction = prediction_service.predict_from_url(VALID_URL)

    assert isinstance(prediction, float)
    assert prediction == 100.0


def test_predict_from_url_scraping_error(prediction_service):
    """Test handling of scraping errors"""
    url = "https://www.grailed.com/listings/error"

    with pytest.raises(HTTPException) as exc_info:
        prediction_service.predict_from_url(url)

    assert exc_info.value.status_code == 422
    assert "Failed to scrape listing" in str(exc_info.value.detail)


def test_predict_from_form_success(prediction_service):
    """Test successful prediction from form data"""
    prediction = prediction_service.predict_from_form(VALID_LISTING_DATA)

    assert isinstance(prediction, float)
    assert prediction == 100.0


def test_predict_from_form_handles_missing_hashtags(prediction_service):
    """Test that prediction works with missing hashtags"""
    data = VALID_LISTING_DATA.copy()
    data["hashtags"] = None

    prediction = prediction_service.predict_from_form(data)

    assert isinstance(prediction, float)
    assert prediction == 100.0
