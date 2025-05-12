#!.venv/bin/python
from kafka import KafkaConsumer
import os

kafka_server_bash_command = "kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
bootstrap_server = os.popen(kafka_server_bash_command).read().strip()
print(f"Bootstrap servers: {bootstrap_server}")

try:
    consumer = KafkaConsumer(
        'network-traffic',
        bootstrap_servers=f"{bootstrap_server}:9094",
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='my-group',
        value_deserializer=lambda x: x.decode('utf-8')
    )

    print("Listening for messages...")
    for message in consumer:
        print(f"Received: {message.value}")
except Exception as e:
    print(f"An error occurred: {e}")