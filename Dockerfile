# Stage 1: Export requirements
FROM python:3.11-slim AS requirements-stage

WORKDIR /tmp

RUN pip install poetry && \
    poetry self add poetry-plugin-export

COPY pyproject.toml poetry.lock* /tmp/

# Export only API and ML dependencies, excluding streamlit and scraper groups
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --with web --with scraper


# Stage 2: Build the API service
FROM python:3.11-slim

WORKDIR /code

# Copy only the necessary modules for the API
COPY /api ./api
COPY /graildient_descent ./graildient_descent
COPY /data_collection ./data_collection
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

# Set environment variables
ENV PYTHONPATH=/code
ENV S3_MODEL_PATH=""
ENV S3_MODELS_BUCKET="graildient-models"

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r requirements.txt && \
    apt-get remove -y gcc && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Command to run the FastAPI application
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
