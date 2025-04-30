minikube start --memory=4096 --cpus=8 --disk-size=40G 
kubectl cluster-info
kubectl create -f stack.yml