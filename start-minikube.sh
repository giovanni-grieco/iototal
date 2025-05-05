#pre autorizzazione
sudo -v

#lancia minikube
minikube start --memory=4096 --cpus=8 --disk-size=40G 

#apre la dashboard in background
minikube dashboard > dashboard.log 2>&1 &

#lancia il tunnel in background
minikube tunnel > tunnel.log 2>&1 &