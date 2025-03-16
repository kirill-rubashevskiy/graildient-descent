#!/bin/bash

# This script builds Docker images for the Graildient Descent app
# for Docker Desktop Kubernetes

set -e

# Navigate to the project root directory (parent of kubernetes/)
cd ..

# Build the API image
echo "Building API image..."
docker build -t graildient-descent-api:latest -f Dockerfile .

# Build the Celery image
echo "Building Celery image..."
docker build -t graildient-descent-celery:latest -f Dockerfile.celery .

# Build the Streamlit image
echo "Building Streamlit image..."
docker build -t graildient-descent-streamlit:latest -f Dockerfile.streamlit .

echo "All images built successfully"
echo "You can now apply the Kubernetes manifests."
