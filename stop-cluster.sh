kubectl delete -f hadoop.yml -n big-data
kubectl delete -f kafka.yml -n big-data
kubectl delete -f spark.yml -n big-data
kubectl delete namespace big-data


