KAFKA_SERVER=$(kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
KAFKA_SERVER="${KAFKA_SERVER}:9094"


sudo .venv/bin/python3 kafka-sniffer-producer.py --kafka-server $KAFKA_SERVER