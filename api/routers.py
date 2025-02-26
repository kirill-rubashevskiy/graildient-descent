from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from api.config import logger
from api.models import (
    Category,
    Condition,
    Department,
    Listing,
    ListingUrl,
    PredictionResponse,
    PredictionTask,
    Size,
    Subcategory,
)
from celery_tasks.worker import app, predict_existing_listing, predict_new_listing


router = APIRouter(prefix="/api/v1")


@router.post(
    "/predictions/url/submit",
    response_model=PredictionTask,
)
async def submit_predict_existing_listing(listing_url: ListingUrl):
    """Predict price for an existing Grailed listing using its URL."""
    try:
        # Submit task to Celery worker
        task = predict_existing_listing.delay(str(listing_url.url))

        # Return task ID for later retrieval
        return {
            "task_id": task.id,
            "status": "PENDING",
            "submitted_at": task.date_done.isoformat() if task.date_done else None,
        }
    except Exception as e:
        logger.error(f"Error submitting prediction task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/predictions/form/submit",
    response_model=PredictionTask,
)
async def submit_predict_new_listing(listing: Listing):
    """
    Submit a new prediction task to the queue and return a task ID.
    This is a non-blocking operation.
    """
    try:
        # Submit task to Celery worker
        task = predict_new_listing.delay(listing.dict())

        # Return task ID for later retrieval
        return {
            "task_id": task.id,
            "status": "PENDING",
            "submitted_at": task.date_done.isoformat() if task.date_done else None,
        }
    except Exception as e:
        logger.error(f"Error submitting prediction task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get(
    "/predictions/{task_id}",
    response_model=PredictionResponse,
)
async def get_prediction_result(task_id: str):
    """
    Get the result of a previously submitted prediction task.
    """
    try:
        task_result = AsyncResult(task_id, app=app)

        if task_result.status == "PENDING":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED, detail="Task is still processing"
            )
        elif task_result.status == "FAILURE":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Task failed: {str(task_result.result)}",
            )

        # Get the completed prediction
        prediction_data = task_result.result

        # Return in expected format
        return {
            "prediction_id": task_id,
            "predicted_price": prediction_data["predicted_price"],
            "metadata": prediction_data["metadata"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get the current status of a prediction task."""
    task_result = AsyncResult(task_id, app=app)

    return {
        "task_id": task_id,
        "status": task_result.status,
        "ready": task_result.ready(),
        "completed_at": (
            task_result.date_done.isoformat() if task_result.date_done else None
        ),
    }


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


# @router.get("/models/info")
# async def get_model_info(request: Request):
#     """Get information about the currently deployed model."""
#     prediction_service = request.app.state.prediction_service
#     return {
#         "model_name": prediction_service.model.model_name,
#         "model_type": prediction_service.model.estimator_class,
#         "features": {
#             "tabular": prediction_service.model.use_tab_features,
#             "text": prediction_service.model.use_text_features,
#         },
#         "metrics": prediction_service.metrics,
#     }
