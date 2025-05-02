kubectl run kafka-client --rm -ti --image bitnami/kafka:3.1.0 -- bash -c '
cd /opt/bitnami/kafka/bin \
kafka-console-producer.sh \
    --topic test \
    --bootstrap-server 

