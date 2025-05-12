kubectl cluster-info

#externalAccess.enabled=true
#externalAccess.broker.service.type=LoadBalancer
#externalAccess.controller.service.type=LoadBalancer
#externalAccess.broker.service.ports.external=9094
#externalAccess.controller.service.containerPorts.external=9094
#defaultInitContainers.autoDiscovery.enabled=true
#serviceAccount.create=true
#rbac.create=true

kubectl create namespace iototal

kubectl apply -f k8s/minio-dev.yaml

helm install iototal oci://registry-1.docker.io/bitnamicharts/kafka \
    --set controller.automountServiceAccountToken=true \
    --set broker.automountServiceAccountToken=true \
    --set externalAccess.enabled=true \
    --set externalAccess.broker.service.type=LoadBalancer \
    --set externalAccess.controller.service.type=LoadBalancer \
    --set externalAccess.broker.service.ports.external=9094 \
    --set externalAccess.controller.service.containerPorts.external=9094 \
    --set defaultInitContainers.autoDiscovery.enabled=true \
    --set serviceAccount.create=true \
    --set rbac.create=true \
    --set listeners.client.protocol=plaintext \
    --set listeners.controller.protocol=plaintext \
    --set listeners.interbroker.protocol=plaintext \
    --set listeners.external.protocol=plaintext \

printf "Remember to start a tunnel to talk outside of cluster\n"
printf "e.g. minikube tunnel\n"

kubectl create serviceaccount spark
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark --namespace=default


# Start HDFS??
# HDFS è nato prima di kubernetes, non è l'ideale, non ci sono soluzioni pre-confezionate a quanto pare