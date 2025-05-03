#!/bin/bash

CLUSTER_IP=$(minikube ip)


# Submit the Spark job
echo "Submitting Spark job..."
spark-submit \
    --master k8s://https://$CLUSTER_IP:8443 \
    --deploy-mode cluster \
    --name iototal-spark \
    --conf spark.executor.instances=1 \
    --conf spark.kubernetes.container.image=apache/spark:latest \
    --conf spark.kubernetes.namespace=default \
    --conf spark.kubernetes.local.dirs.tmpfs=true \
    --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
    --conf spark.kubernetes.authenticate.executor.serviceAccountName=spark \
    --conf spark.kubernetes.driver.volumes.persistentVolumeClaim.spark-files.options.claimName=spark-upload-pvc \
    --conf spark.kubernetes.driver.volumes.persistentVolumeClaim.spark-files.mount.path=/mnt/files \
    --conf spark.kubernetes.driver.volumes.persistentVolumeClaim.spark-files.mount.readOnly=false \
    --conf spark.kubernetes.executor.volumes.persistentVolumeClaim.spark-files.options.claimName=spark-upload-pvc \
    --conf spark.kubernetes.executor.volumes.persistentVolumeClaim.spark-files.mount.path=/mnt/files \
    --conf spark.kubernetes.executor.volumes.persistentVolumeClaim.spark-files.mount.readOnly=false \
    --conf spark.kubernetes.file.upload.path=/mnt/files \
    https://game-hub.it/iototal/spark-job.py \

echo "Job submitted. Check status with 'kubectl get pods'"