#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-spark-job.py>"
    exit 1
fi

CLUSTER_IP=$(minikube ip)
SPARK_JOB_FILE=$1


# Create ConfigMap from your Python file
echo "Creating ConfigMap from spark-job.py..."
kubectl delete configmap spark-job-cm 2>/dev/null || true
kubectl create configmap spark-job-cm --from-file=spark-job.py=$(pwd)/$SPARK_JOB_FILE

# Create pod template
cat > driver-pod-template.yaml << EOF
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: spark-kubernetes-driver
    volumeMounts:
    - name: spark-job-volume
      mountPath: /opt/spark/work-dir/job
  volumes:
  - name: spark-job-volume
    configMap:
      name: spark-job-cm
EOF

# Submit the Spark job
echo "Submitting Spark job..."
spark-submit \
    --master k8s://https://$CLUSTER_IP:8443 \
    --deploy-mode cluster \
    --name iototal-spark \
    --conf spark.executor.instances=1 \
    --conf spark.kubernetes.container.image=apache/spark:latest \
    --conf spark.kubernetes.namespace=default \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.executor.serviceAccountName=spark \
    --conf spark.kubernetes.driver.podTemplateFile=driver-pod-template.yaml \
    --conf spark.kubernetes.local.dirs.tmpfs=true \
    --conf spark.driver.memory=2g \
    --conf spark.executor.memory=2g \
    --conf spark.memory.fraction=0.8 \
    --conf spark.memory.storageFraction=0.5 \
    --conf spark.speculation=false \
    --conf spark.sql.shuffle.partitions=10 \
    --conf spark.sql.adaptive.enabled=true \
    --conf spark.sql.adaptive.coalescePartitions.enabled=true \
    local:///opt/spark/work-dir/job/spark-job.py

echo "Job submitted. Check status with 'kubectl get pods'"