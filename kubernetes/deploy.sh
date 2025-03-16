#!/bin/bash

# This script deploys the Graildient Descent application to Docker Desktop Kubernetes

set -e

# Check if Kubernetes is running in Docker Desktop
if ! kubectl cluster-info &> /dev/null; then
    echo "Kubernetes is not running. Please enable Kubernetes in Docker Desktop."
    exit 1
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Apply ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

# Apply infrastructure services first
echo "Deploying PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

echo "Deploying RabbitMQ..."
kubectl apply -f rabbitmq-deployment.yaml

# Wait for infrastructure to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/postgres \
  --timeout=300s

echo "Waiting for RabbitMQ to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/rabbitmq \
  --timeout=300s

# Apply application deployments
echo "Deploying API service..."
kubectl apply -f api-deployment.yaml

echo "Deploying Celery worker..."
kubectl apply -f celery-deployment.yaml

echo "Deploying Celery Flower..."
kubectl apply -f celery-flower-deployment.yaml

echo "Deploying Streamlit frontend..."
kubectl apply -f streamlit-deployment.yaml

# Wait for application services to be ready
echo "Waiting for API to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/api \
  --timeout=300s

echo "Waiting for Celery Flower to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/celery-flower \
  --timeout=300s

echo "Waiting for Streamlit to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/streamlit \
  --timeout=300s

echo "Deployment complete!"
echo "======================================="
echo "You can access your application using:"
echo "API: http://localhost:30000/api"
echo "API Docs: http://localhost:30000/docs"
echo "Streamlit: http://localhost:30001"
echo "Celery Flower: http://localhost:30002"
echo "======================================="
