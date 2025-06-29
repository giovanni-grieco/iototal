#pre autorizzazione
sudo -v

#lancia minikube
minikube start --memory=24000 --cpus=14 --disk-size=40G 

minikube ssh "sudo mkdir -p /data/ivy-cache && sudo chown -R 185:185 /data/ivy-cache"

#apre la dashboard in background
minikube dashboard > dashboard.log 2>&1 &

#lancia il tunnel in background
minikube tunnel > tunnel.log 2>&1 &
