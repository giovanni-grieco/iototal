helm uninstall iototal

kubectl delete clusterrolebinding spark-role
kubectl delete serviceaccount spark
kubectl delete -f k8s/minio-dev.yaml
kubectl delete -f k8s/secrets.yaml
kubectl delete pods --all
kubectl delete pvc --all
kubectl delete pv --all
#stop HDFS ??


