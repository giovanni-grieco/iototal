#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-spark-job.py>"
    exit 1
fi

CLUSTER_IP=$(minikube ip) #replace with a remote kubernetes cluster IP if needed
#CLUSTER_IP=<your_remote_cluster_ip>
SPARK_JOB_FILE=$1

if [ ! -f "$SPARK_JOB_FILE" ]; then
    echo "File $SPARK_JOB_FILE not found!"
    exit 1
fi
echo "Starting Spark job submission..."
echo "Cluster IP: $CLUSTER_IP"
echo "Spark job file: $SPARK_JOB_FILE"

# Create ConfigMap from your Python file
echo "Creating ConfigMap from spark-job.py..."
kubectl delete configmap spark-job-cm 2>/dev/null || true
kubectl create configmap spark-job-cm --from-file=spark-job.py=$(pwd)/$SPARK_JOB_FILE

# Submit the Spark job
echo "Submitting Spark job..."
spark-submit \
    --master k8s://https://$CLUSTER_IP:8443 \
    --deploy-mode cluster \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5,org.apache.hadoop:hadoop-aws:3.3.4 \
    --name iototal-spark \
    --conf spark.executor.instances=1 \
    --conf spark.kubernetes.container.image=henderson43/spark-iototal:latest \
    --conf spark.kubernetes.namespace=default \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.executor.serviceAccountName=spark \
    --conf spark.kubernetes.driver.podTemplateFile=k8s/driver-pod-template.yaml \
    --conf spark.kubernetes.executor.podTemplateFile=k8s/executor-pod-template.yaml \
    --conf spark.kubernetes.local.dirs.tmpfs=true \
    --conf spark.driver.memory=4g \
    --conf spark.driver.cores=4 \
    --conf spark.executor.memory=16g \
    --conf spark.executor.cores=10 \
    local:///opt/spark/work-dir/job/spark-job.py

echo "Job submitted. Check status with 'kubectl get all'"
