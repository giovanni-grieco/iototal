#!/bin/bash

# Configuration variables (should match start-gke-cluster.sh)
PROJECT_ID="amiable-alcove-464414-m1"  # Replace with your actual GCP project ID
CLUSTER_NAME="iototal-cluster"
ZONE="europe-west1-b"

echo "=== Starting GKE cluster deletion ==="
echo "Project ID: $PROJECT_ID"
echo "Cluster Name: $CLUSTER_NAME"
echo "Zone: $ZONE"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Get cluster credentials (in case not already configured)
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE 2>/dev/null || true

# Clean up Kubernetes resources first
echo "Cleaning up Kubernetes resources..."

# Clean up Spark pods and jobs
echo "Cleaning up Spark resources..."
kubectl delete pods -l spark-role=driver --force --grace-period=0 2>/dev/null || true
kubectl delete pods -l spark-role=executor --force --grace-period=0 2>/dev/null || true
kubectl delete configmap spark-job-cm 2>/dev/null || true

# Uninstall Helm releases
echo "Uninstalling Helm releases..."
helm uninstall iototal 2>/dev/null || true

# Delete Kubernetes resources
echo "Deleting Kubernetes resources..."
kubectl delete clusterrolebinding spark-role 2>/dev/null || true
kubectl delete serviceaccount spark 2>/dev/null || true
kubectl delete -f k8s/minio-dev-gke.yaml 2>/dev/null || true
# Note: no ivy-cache-volume to delete since we use emptyDir
kubectl delete -f k8s/secrets.yaml 2>/dev/null || true

# Wait a moment for resources to be deleted
echo "Waiting for resources to be cleaned up..."
sleep 30

# Delete the GKE cluster
echo "Deleting GKE cluster '$CLUSTER_NAME'..."
gcloud container clusters delete $CLUSTER_NAME \
    --zone=$ZONE \
    --quiet

# Clean up any remaining LoadBalancer resources (optional)
echo "Checking for remaining LoadBalancer resources..."
gcloud compute forwarding-rules list --format="table(name,region,target)" --filter="description~'$CLUSTER_NAME'" 2>/dev/null || true

echo "=== GKE cluster deletion complete! ==="
echo ""
echo "Note: It may take a few minutes for all cloud resources to be fully deleted."
echo "Check the GCP Console to verify all resources have been removed."
echo ""
echo "To verify deletion, run:"
echo "  gcloud container clusters list"
