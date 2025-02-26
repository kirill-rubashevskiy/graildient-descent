import logging
import os
from datetime import datetime

from celery import Celery, signals

from api.services import PredictionService
from data_collection.scraper import GrailedListingScraper
from graildient_descent.model import Model


# Configure Celery
app = Celery(
    "graildient_descent",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://"),
)
app.conf.worker_proc_alive_timeout = 30

# Global variable to store the model in each worker
prediction_service = None


@signals.worker_process_init.connect
def init_worker_process(**kwargs):
    """
    Initialize the model when the worker starts.
    This ensures each Celery worker has its own model instance.
    """
    global prediction_service

    S3_MODEL_PATH = os.getenv("S3_MODEL_PATH")
    S3_MODELS_BUCKET = os.getenv("S3_MODELS_BUCKET")

    # Load model from S3
    try:
        model, metrics = Model.load_model(
            path=S3_MODEL_PATH, from_s3=True, bucket_name=S3_MODELS_BUCKET
        )
        scraper = GrailedListingScraper()
        prediction_service = PredictionService(model, metrics, scraper)
        logging.info("Successfully initialized application services")
    except Exception as e:
        logging.error(f"Failed to initialize services: {str(e)}")
        raise


@app.task(name="predict_new_listing")
def predict_new_listing(listing_data: dict):
    try:
        prediction = prediction_service.predict_from_form(listing_data)
        return dict(
            predicted_price=int(round(prediction)),
            metadata=dict(
                model_name=prediction_service.model.model_name,
                prediction_timestamp=datetime.utcnow().isoformat(),
            ),
        )
    except Exception as e:
        logging.error(f"Error processing form prediction: {str(e)}")


@app.task(name="predict_existing_listing")
def predict_existing_listing(listing_url: str):
    try:
        prediction = prediction_service.predict_from_url(listing_url)
        return dict(
            predicted_price=int(round(prediction)),
            metadata=dict(
                model_name=prediction_service.model.model_name,
                prediction_timestamp=datetime.utcnow().isoformat(),
            ),
        )
    except Exception as e:
        logging.error(f"Error processing prediction url: {str(e)}")


app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)
