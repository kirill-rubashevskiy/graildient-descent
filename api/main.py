from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from api.config import S3_MODEL_PATH, S3_MODELS_BUCKET, logger
from api.logging.middleware import setup_request_logging
from api.routers import router
from api.services import PredictionService
from data_collection.scraper import GrailedListingScraper
from graildient_descent.model import Model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles initialization and cleanup of application resources.
    """
    # Startup: Initialize services
    try:
        model, metrics = Model.load_model(
            path=S3_MODEL_PATH, from_s3=True, bucket_name=S3_MODELS_BUCKET
        )
        scraper = GrailedListingScraper()
        prediction_service = PredictionService(model, metrics, scraper)
        app.state.prediction_service = prediction_service
        logger.info("Successfully initialized application services")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

    yield


app = FastAPI(
    title="Graildient Descent API",
    description="API for predicting Grailed listing prices",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up logging
setup_request_logging(app)

# Include routers
app.include_router(router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": hasattr(app.state, "prediction_service"),
    }
