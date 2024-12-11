import pytest

from api.models import PredictionResponse
from api.utils import generate_prediction_response


@pytest.mark.parametrize(
    "prediction,model_name",
    [
        (100.5, "test_model"),
        (99.99, "catboost_v1"),
        (0.01, "minimal_model"),
        (9999.99, "large_model"),
    ],
)
def test_generate_prediction_response_values(prediction, model_name):
    """Test that generate_prediction_response returns correct values for different inputs"""
    response = generate_prediction_response(prediction, model_name)

    assert isinstance(response, PredictionResponse)
    assert isinstance(response.prediction_id, str)
    assert response.prediction_id.startswith("pred_")
    assert response.predicted_price == round(prediction)
    assert response.metadata["model_name"] == model_name
    assert isinstance(response.metadata["prediction_timestamp"], str)


def test_metadata_structure():
    """Test that metadata dictionary has the correct structure"""
    response = generate_prediction_response(100.0, "test_model")

    required_keys = {"model_name", "prediction_timestamp"}
    assert set(response.metadata.keys()) == required_keys

    # Check that no extra keys are present
    assert len(response.metadata) == len(required_keys)
