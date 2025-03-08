from datetime import datetime

from fastapi import FastAPI

from api.logging.middleware import setup_request_logging
from api.routers import router


app = FastAPI(
    title="Graildient Descent API",
    description="API for predicting Grailed listing prices",
    version="1.0.0",
)

# Set up logging
setup_request_logging(app)

# Include routers
app.include_router(router)


@app.get("/api/health")
async def health_check():
    from celery_tasks.worker import app

    worker_status = app.control.inspect().ping() or {}
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        # "model_loaded": hasattr(app.state, "prediction_service"),
        "workers": list(worker_status.keys()) if worker_status else [],
        "worker_count": len(worker_status),
    }
