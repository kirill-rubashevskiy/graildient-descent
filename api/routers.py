from fastapi import APIRouter, HTTPException, Request, status

from api.config import logger
from api.models import (
    Category,
    Condition,
    Department,
    Listing,
    ListingUrl,
    PredictionResponse,
    Size,
    Subcategory,
)
from api.utils import generate_prediction_response


router = APIRouter(prefix="/api/v1")


@router.post(
    "/predictions/url",
    response_model=PredictionResponse,
)
async def predict_existing_listing(listing_url: ListingUrl, request: Request):
    """Predict price for an existing Grailed listing using its URL."""
    try:
        prediction_service = request.app.state.prediction_service
        prediction = prediction_service.predict_from_url(str(listing_url.url))
        return generate_prediction_response(
            prediction, prediction_service.model.model_name
        )
    except HTTPException as he:
        logger.error(f"HTTP error processing URL prediction: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Error processing URL prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/predictions/form",
    response_model=PredictionResponse,
)
async def predict_new_listing(listing: Listing, request: Request):
    """Predict price for a new listing based on provided features."""
    try:
        prediction_service = request.app.state.prediction_service
        prediction = prediction_service.predict_from_form(listing.dict())
        return generate_prediction_response(
            prediction, prediction_service.model.model_name
        )
    except Exception as e:
        logger.error(f"Error processing form prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/docs/options")
async def get_valid_options():
    """Get valid options for all categorical fields."""
    return {
        "departments": [e.value for e in Department],
        "categories": [e.value for e in Category],
        "subcategories": [e.value for e in Subcategory],
        "conditions": [e.value for e in Condition],
        "sizes": [e.value for e in Size],
    }


@router.get("/models/info")
async def get_model_info(request: Request):
    """Get information about the currently deployed model."""
    prediction_service = request.app.state.prediction_service
    return {
        "model_name": prediction_service.model.model_name,
        "model_type": prediction_service.model.estimator_class,
        "features": {
            "tabular": prediction_service.model.use_tab_features,
            "text": prediction_service.model.use_text_features,
        },
        "metrics": prediction_service.metrics,
    }
