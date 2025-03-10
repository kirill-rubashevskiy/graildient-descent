#!/bin/bash

# This script builds Docker images for the Graildient Descent app
# and loads them into Minikube's Docker daemon.

set -e

# Start Minikube if it's not running
if ! minikube status > /dev/null 2>&1; then
    echo "Starting Minikube..."
    minikube start
fi

# Point Docker CLI to Minikube's Docker daemon
echo "Configuring Docker CLI to use Minikube's Docker daemon..."
eval $(minikube docker-env)

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

# Navigate to the project root directory (parent of kubernetes/)
cd ..

echo "All images built successfully and loaded into Minikube's Docker daemon."
echo "You can now apply the Kubernetes manifests."
