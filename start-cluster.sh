kubectl cluster-info

#externalAccess.enabled=true
#externalAccess.broker.service.type=LoadBalancer
#externalAccess.controller.service.type=LoadBalancer
#externalAccess.broker.service.ports.external=9094
#externalAccess.controller.service.containerPorts.external=9094
#defaultInitContainers.autoDiscovery.enabled=true
#serviceAccount.create=true
#rbac.create=true

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

kubectl apply -f spark-pv.yaml

kubectl create serviceaccount spark
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark --namespace=default

echo "=========================================================="
echo "Minikube started successfully."
echo ""
echo "To enable external access to LoadBalancer services,"
echo "please run the following command in a separate terminal:"
echo ""
echo "    minikube tunnel"
echo ""
echo "This command requires sudo privileges and will continue"
echo "running until you terminate it with Ctrl+C."
echo "=========================================================="


# Start HDFS??