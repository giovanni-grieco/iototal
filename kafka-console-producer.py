from kafka import KafkaProducer
import os

kafka_server_bash_command = "kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
bootstrap_server = os.popen(kafka_server_bash_command).read().strip()
print(f"Bootstrap servers: {bootstrap_server}")

try:
    producer = KafkaProducer(bootstrap_servers=f"{bootstrap_server}:9094")

    while True:
        message = input("Enter message to send to Kafka topic (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        producer.send('test-topic', value=message.encode('utf-8'))
        print(f"Sent: {message}")
except Exception as e:
    print(f"An error occurred: {e}")
