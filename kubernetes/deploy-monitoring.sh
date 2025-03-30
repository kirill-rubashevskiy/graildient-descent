#!/bin/bash

# This script deploys monitoring components to Kubernetes

set -e

# Create the Prometheus config
echo "Creating Prometheus ConfigMap..."
kubectl apply -f prometheus-config.yaml

# Apply monitoring resources
echo "Deploying node-exporter..."
kubectl apply -f node-exporter.yaml

echo "Deploying RabbitMQ exporter..."
kubectl apply -f rabbitmq-exporter.yaml

echo "Deploying PostgreSQL exporter..."
kubectl apply -f postgres-exporter.yaml

echo "Deploying Prometheus..."
kubectl apply -f prometheus-deployment.yaml

echo "Creating Grafana datasources ConfigMap..."
kubectl apply -f grafana-datasources.yaml

echo "Deploying Grafana..."
kubectl apply -f grafana-deployment.yaml

echo "Applying monitoring ingress..."
kubectl apply -f monitoring-ingress.yaml

echo "Monitoring deployment completed!"
echo "======================================="
echo "You can access monitoring at:"
echo "Prometheus: http://graildient.local/prometheus"
echo "Grafana: http://graildient.local/grafana"
echo "Default Grafana credentials: admin/admin"
echo "======================================="
echo "Recommended Grafana dashboards to import:"
echo "- Node Exporter: 1860"
echo "- RabbitMQ: 10991"
echo "- PostgreSQL: 9628"
echo "- FastAPI: 14810"
echo "======================================="
