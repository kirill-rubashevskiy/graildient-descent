from datetime import datetime

import uvicorn
from fastapi import FastAPI

from api.config import S3_MODEL_PATH, S3_MODELS_BUCKET, logger
from api.routers import router
from api.services import PredictionService
from data_collection.scraper import GrailedListingScraper
from graildient_descent.model import Model


app = FastAPI(
    title="Graildient Descent API",
    description="API for predicting Grailed listing prices",
    version="1.0.0",
)

# Initialize services
try:
    model, metrics = Model.load_model(
        path=S3_MODEL_PATH, from_s3=True, bucket_name=S3_MODELS_BUCKET
    )
    scraper = GrailedListingScraper()
    prediction_service = PredictionService(model, metrics, scraper)
    app.state.prediction_service = prediction_service
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

# Include routers
app.include_router(router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": model is not None,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
