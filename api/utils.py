from datetime import datetime

from api.models import PredictionResponse


def generate_prediction_response(
    prediction: float, model_name: str
) -> PredictionResponse:
    """Generate standardized prediction response."""
    return PredictionResponse(
        prediction_id=f"pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        predicted_price=int(round(prediction)),
        metadata={
            "model_name": model_name,
            "prediction_timestamp": datetime.utcnow().isoformat(),
        },
    )
