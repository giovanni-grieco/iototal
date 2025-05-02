kubectl cluster-info
kubectl create namespace big-data

kubectl apply -f hadoop.yml -n big-data
kubectl apply -f kafka.yml -n big-data
kubectl apply -f spark.yml -n big-data