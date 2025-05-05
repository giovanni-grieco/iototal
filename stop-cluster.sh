helm uninstall iototal

kubectl delete clusterrolebinding spark-role
kubectl delete serviceaccount spark
kubectl delete pods --all
kubectl delete pvc --all
kubectl delete pv --all
#stop HDFS ??


