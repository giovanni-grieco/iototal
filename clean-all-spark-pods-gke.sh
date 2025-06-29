#!/bin/bash

echo "Cleaning up Spark pods and resources on GKE..."

# Delete Spark driver and executor pods
echo "Deleting Spark driver pods..."
kubectl delete pods -l spark-role=driver --force --grace-period=0 2>/dev/null || true

echo "Deleting Spark executor pods..."
kubectl delete pods -l spark-role=executor --force --grace-period=0 2>/dev/null || true

# Delete any completed or failed pods
echo "Deleting completed/failed pods..."
kubectl delete pods --field-selector=status.phase=Succeeded --force --grace-period=0 2>/dev/null || true
kubectl delete pods --field-selector=status.phase=Failed --force --grace-period=0 2>/dev/null || true

# Delete ConfigMaps
echo "Deleting Spark ConfigMaps..."
kubectl delete configmap spark-job-cm 2>/dev/null || true

# Show remaining pods
echo "Remaining pods:"
kubectl get pods

echo "Spark cleanup complete!"
