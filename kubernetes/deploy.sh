#!/bin/bash

# This script deploys the Graildient Descent application to Minikube

set -e

# Ensure Minikube is running
if ! minikube status > /dev/null 2>&1; then
    echo "Minikube is not running. Starting..."
    minikube start
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Apply ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

# Not using Secrets for this deployment
echo "Skipping Secrets for the initial deployment."

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

echo "Deploying Streamlit frontend..."
kubectl apply -f streamlit-deployment.yaml

# Wait for application services to be ready
echo "Waiting for API to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/api \
  --timeout=300s

echo "Waiting for Streamlit to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/streamlit \
  --timeout=300s

# Deploy NGINX last
echo "Deploying NGINX..."
kubectl apply -f nginx-deployment.yaml

# Get the NGINX NodePort URL
echo "Waiting for NGINX to be ready..."
kubectl wait --namespace graildient-descent \
  --for=condition=available deployment/nginx \
  --timeout=300s

NGINX_URL=$(minikube service nginx -n graildient-descent --url)

echo "Deployment complete!"
echo "======================================="
echo "You can access your application using:"
echo "API: $NGINX_URL"
echo "Streamlit: $NGINX_URL (add host header: app.graildient-descent.local)"
echo "======================================="
echo "For local testing, add these entries to your /etc/hosts file:"
echo "$(minikube ip) api.graildient-descent.local"
echo "$(minikube ip) app.graildient-descent.local"
