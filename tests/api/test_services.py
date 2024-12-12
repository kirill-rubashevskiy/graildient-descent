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
    """Test handling of scraping errors with detailed error messages."""
    url = "https://www.grailed.com/listings/error"

    # Mock the scraper to return an error response
    prediction_service.scraper.get_listing_data.return_value = {
        "error": "HTTPError",
        "status_code": 403,
        "message": "Access denied",
    }

    with pytest.raises(HTTPException) as exc_info:
        prediction_service.predict_from_url(url)

    assert exc_info.value.status_code == 422
    # Check that all error components are present in the detail message
    error_detail = exc_info.value.detail
    assert "Error type: HTTPError" in error_detail
    assert "Status code: 403" in error_detail
    assert "Message: Access denied" in error_detail


def test_predict_from_url_scraping_error_minimal(prediction_service):
    """Test handling of scraping errors with minimal error information."""
    url = "https://www.grailed.com/listings/error"

    # Mock the scraper to return an error response with minimal information
    prediction_service.scraper.get_listing_data.return_value = {
        "error": "ConnectionError",
        "message": "Connection timeout",
    }

    with pytest.raises(HTTPException) as exc_info:
        prediction_service.predict_from_url(url)

    assert exc_info.value.status_code == 422
    error_detail = exc_info.value.detail
    assert "Error type: ConnectionError" in error_detail
    assert "Message: Connection timeout" in error_detail
    assert "Status code" not in error_detail


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
