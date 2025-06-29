#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-spark-job.py>"
    exit 1
fi

# Configuration - should match your GKE cluster settings
PROJECT_ID="amiable-alcove-464414-m1"  # Replace with your actual GCP project ID
CLUSTER_NAME="iototal-cluster"
ZONE="europe-west1-b"

SPARK_JOB_FILE=$1

if [ ! -f "$SPARK_JOB_FILE" ]; then
    echo "File $SPARK_JOB_FILE not found!"
    exit 1
fi

# Get GKE cluster endpoint
echo "Getting GKE cluster information..."
CLUSTER_ENDPOINT=$(gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE --format="value(endpoint)")
if [ -z "$CLUSTER_ENDPOINT" ]; then
    echo "Error: Could not get cluster endpoint. Make sure the cluster is running."
    exit 1
fi

echo "Starting Spark job submission..."
echo "Cluster Endpoint: $CLUSTER_ENDPOINT"
echo "Spark job file: $SPARK_JOB_FILE"

# Ensure we have the right cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Create ConfigMap from your Python file
echo "Creating ConfigMap from spark-job.py..."
kubectl delete configmap spark-job-cm 2>/dev/null || true
kubectl create configmap spark-job-cm --from-file=spark-job.py=$(pwd)/$SPARK_JOB_FILE

# Submit the Spark job
echo "Submitting Spark job..."
spark-submit \
    --master k8s://https://$CLUSTER_ENDPOINT:443 \
    --deploy-mode cluster \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5,org.apache.hadoop:hadoop-aws:3.3.4 \
    --name iototal-spark \
    --conf spark.executor.instances=2 \
    --conf spark.kubernetes.container.image=henderson43/spark-iototal:latest \
    --conf spark.kubernetes.namespace=default \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.executor.serviceAccountName=spark \
    --conf spark.kubernetes.driver.podTemplateFile=k8s/driver-pod-template-gke.yaml \
    --conf spark.kubernetes.executor.podTemplateFile=k8s/executor-pod-template-gke.yaml \
    --conf spark.kubernetes.local.dirs.tmpfs=true \
    --conf spark.driver.memory=4g \
    --conf spark.driver.cores=2 \
    --conf spark.executor.memory=8g \
    --conf spark.executor.cores=2 \
    local:///opt/spark/work-dir/job/spark-job.py

echo "Job submitted. Check status with 'kubectl get all'"
echo "To see driver logs: kubectl logs -l spark-role=driver"
echo "To see executor logs: kubectl logs -l spark-role=executor"
