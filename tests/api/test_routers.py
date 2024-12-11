import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import Category, Condition, Department, Size, Subcategory
from tests.api.conftest import VALID_LISTING_DATA, VALID_URL


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def app_with_mocked_service(prediction_service):
    app.state.prediction_service = prediction_service
    return app


# URL Prediction Tests
def test_predict_from_url_success(client, app_with_mocked_service):
    """Test successful prediction from URL"""
    response = client.post("/api/v1/predictions/url", json={"url": VALID_URL})

    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert "predicted_price" in data
    assert data["predicted_price"] == 100.0
    assert data["metadata"]["model_name"] == "mock_model"


def test_predict_from_url_invalid_url(client, app_with_mocked_service):
    """Test prediction with invalid URL"""
    response = client.post("/api/v1/predictions/url", json={"url": "not-a-url"})

    assert response.status_code == 422
    assert "url" in response.json()["detail"][0]["loc"]


def test_predict_from_url_error(client, app_with_mocked_service, prediction_service):
    """Test handling of prediction service errors"""
    prediction_service.predict_from_url = Exception("Service error")

    response = client.post("/api/v1/predictions/url", json={"url": VALID_URL})

    assert response.status_code == 500
    assert "detail" in response.json()


# Form Prediction Tests
def test_predict_from_form_success(client, app_with_mocked_service):
    """Test successful prediction from form data"""
    response = client.post("/api/v1/predictions/form", json=VALID_LISTING_DATA)

    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert "predicted_price" in data
    assert data["predicted_price"] == 100.0
    assert data["metadata"]["model_name"] == "mock_model"


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("n_photos", 0),  # Too low
        ("n_photos", 26),  # Too high
        ("item_name", ""),  # Empty string
        ("item_name", "a" * 61),  # Too long
        ("designer", ""),  # Empty string
        ("color", ""),  # Empty string
    ],
)
def test_predict_from_form_invalid_data(
    client, app_with_mocked_service, field, invalid_value
):
    """Test prediction with invalid form data"""
    data = VALID_LISTING_DATA.copy()
    data[field] = invalid_value

    response = client.post("/api/v1/predictions/form", json=data)

    assert response.status_code == 422
    assert field in str(response.json()["detail"])


def test_predict_from_form_missing_fields(client, app_with_mocked_service):
    """Test prediction with missing required fields"""
    incomplete_data = {"designer": "nike", "department": "menswear"}

    response = client.post("/api/v1/predictions/form", json=incomplete_data)

    assert response.status_code == 422


def test_predict_from_form_error(client, app_with_mocked_service, prediction_service):
    """Test handling of prediction service errors"""
    prediction_service.predict_from_form = Exception("Service error")

    response = client.post("/api/v1/predictions/form", json=VALID_LISTING_DATA)

    assert response.status_code == 500
    assert "detail" in response.json()


# Options Endpoint Tests
def test_get_valid_options(client):
    """Test getting valid options for categorical fields"""
    response = client.get("/api/v1/docs/options")

    assert response.status_code == 200
    data = response.json()

    # Verify all enum options are present
    assert set(data.keys()) == {
        "departments",
        "categories",
        "subcategories",
        "conditions",
        "sizes",
    }
    assert set(data["departments"]) == {e.value for e in Department}
    assert set(data["categories"]) == {e.value for e in Category}
    assert set(data["subcategories"]) == {e.value for e in Subcategory}
    assert set(data["conditions"]) == {e.value for e in Condition}
    assert set(data["sizes"]) == {e.value for e in Size}


# Model Info Tests
def test_get_model_info(client, app_with_mocked_service):
    """Test getting model information"""
    response = client.get("/api/v1/models/info")

    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "mock_model"
    assert data["model_type"] == "lr"
    assert data["features"]["tabular"] is True
    assert data["features"]["text"] is False
    assert "metrics" in data
    assert data["metrics"]["rmsle"] == 0.5
    assert data["metrics"]["wape"] == 0.3


# Health Check Tests
def test_health_check(client, app_with_mocked_service):
    """Test health check endpoint"""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert data["status"] == "healthy"


# Error Handling Tests
def test_404_not_found(client):
    """Test handling of non-existent endpoints"""
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404


def test_method_not_allowed(client):
    """Test handling of incorrect HTTP methods"""
    response = client.get("/api/v1/predictions/form")
    assert response.status_code == 405
