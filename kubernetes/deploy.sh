#!/bin/bash

# This script deploys the complete Graildient Descent application to Kubernetes

set -e

# Check if Kubernetes is running
if ! kubectl cluster-info &> /dev/null; then
    echo "Kubernetes is not running. Please ensure your Kubernetes cluster is accessible."
    exit 1
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Check if NGINX Ingress Controller is already installed
if kubectl get ns ingress-nginx &> /dev/null; then
    echo "NGINX Ingress Controller is already installed."
else
    echo "Installing NGINX Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

    # Wait for the Ingress controller to be ready
    echo "Waiting for NGINX Ingress Controller to be ready..."
    kubectl wait --namespace ingress-nginx \
      --for=condition=ready pod \
      --selector=app.kubernetes.io/component=controller \
      --timeout=120s || true
fi

# Apply ConfigMap and Secrets
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

echo "Applying Secrets..."
kubectl apply -f secrets.yaml

# Apply infrastructure services first
echo "Deploying PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

echo "Deploying RabbitMQ..."
kubectl apply -f rabbitmq-deployment.yaml

# Apply application deployments
echo "Deploying API service..."
kubectl apply -f api-deployment.yaml

echo "Deploying Celery worker..."
kubectl apply -f celery-deployment.yaml

echo "Deploying Celery Flower..."
kubectl apply -f celery-flower-deployment.yaml

echo "Deploying Streamlit frontend..."
kubectl apply -f streamlit-deployment.yaml

# Wait a bit for pods to be created
echo "Waiting for pods to be created..."
sleep 10

# Apply the Ingress resource
echo "Applying Ingress resource..."
kubectl apply -f ingress.yaml

# Add hosts entry for local development if it doesn't exist
if ! grep -q "graildient.local" /etc/hosts; then
    echo "Adding graildient.local to /etc/hosts file..."
    echo "Would you like to add 'graildient.local' to your /etc/hosts file? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "127.0.0.1 graildient.local" | sudo tee -a /etc/hosts
        echo "Entry added successfully!"
    else
        echo "Manual action needed: Add '127.0.0.1 graildient.local' to your /etc/hosts file."
    fi
fi

echo "Deployment completed!"
echo "======================================="
echo "You can access your application at:"
echo "API: http://graildient.local/api"
echo "API Docs: http://graildient.local/docs"
echo "Streamlit: http://graildient.local/"
echo "Celery Flower: http://graildient.local/flower"
echo "======================================="
