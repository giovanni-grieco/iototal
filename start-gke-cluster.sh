#!/bin/bash

# Configuration variables
PROJECT_ID="amiable-alcove-464414-m1"  # Replace with your actual GCP project ID
CLUSTER_NAME="iototal-cluster"
ZONE="europe-west1-b"  # Choose your preferred zone
NODE_COUNT=3
MACHINE_TYPE="e2-standard-4"  # 4 vCPU, 16GB RAM
DISK_SIZE="50GB"

echo "=== Starting GKE cluster setup ==="
echo "Project ID: $PROJECT_ID"
echo "Cluster Name: $CLUSTER_NAME"
echo "Zone: $ZONE"
echo "Node Count: $NODE_COUNT"
echo "Machine Type: $MACHINE_TYPE"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo "Error: Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable container.googleapis.com
gcloud services enable storage.googleapis.com

# Create the GKE cluster
echo "Creating GKE cluster '$CLUSTER_NAME'..."
gcloud container clusters create $CLUSTER_NAME \
    --zone=$ZONE \
    --num-nodes=$NODE_COUNT \
    --machine-type=$MACHINE_TYPE \
    --disk-size=$DISK_SIZE \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5 \
    --enable-autorepair \
    --enable-autoupgrade \
    --addons=HorizontalPodAutoscaling,HttpLoadBalancing \
    --enable-network-policy \
    --disk-type=pd-standard

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Verify cluster connection
echo "Verifying cluster connection..."
kubectl cluster-info

# Create namespace if it doesn't exist
kubectl create namespace default --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes resources
echo "Applying Kubernetes resources..."
kubectl create -f k8s/secrets.yaml
kubectl apply -f k8s/minio-dev-gke.yaml
# Note: ivy-cache-volume-gke.yaml is not applied since we use emptyDir

# Install Kafka using Helm
echo "Installing Kafka using Helm..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Kafka with external access
helm install iototal oci://registry-1.docker.io/bitnamicharts/kafka \
    --set controller.automountServiceAccountToken=true \
    --set broker.automountServiceAccountToken=true \
    --set externalAccess.enabled=true \
    --set externalAccess.broker.service.type=LoadBalancer \
    --set externalAccess.controller.service.type=LoadBalancer \
    --set externalAccess.broker.service.ports.external=9094 \
    --set externalAccess.controller.service.containerPorts.external=9094 \
    --set defaultInitContainers.autoDiscovery.enabled=true \
    --set serviceAccount.create=true \
    --set rbac.create=true \
    --set listeners.client.protocol=plaintext \
    --set listeners.controller.protocol=plaintext \
    --set listeners.interbroker.protocol=plaintext \
    --set listeners.external.protocol=plaintext

# Create Spark service account and cluster role binding
echo "Creating Spark service account..."
kubectl create serviceaccount spark
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark --namespace=default

echo "=== GKE cluster setup complete! ==="
echo ""
echo "Cluster Information:"
echo "- Cluster Name: $CLUSTER_NAME"
echo "- Zone: $ZONE"
echo "- Project: $PROJECT_ID"
echo ""
echo "To get cluster status, run:"
echo "  kubectl get all"
echo ""
echo "To get external IPs for services, run:"
echo "  kubectl get services"
echo ""
echo "Note: External LoadBalancer IPs may take a few minutes to be assigned."
