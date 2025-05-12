helm uninstall iototal

kubectl delete clusterrolebinding spark-role
kubectl delete serviceaccount spark
kubectl delete -f k8s/minio-dev.yaml
kubectl delete -f k8s/ivy-cache-volume.yaml
kubectl delete -f k8s/secrets.yaml
#stop HDFS ??


