#!.venv/bin/python

# this producer will read from a CSV file and send each row as a message to a certain topic
# the message rate will be given by the user
from kafka import KafkaProducer
import os
import sys
import time

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} path/to/file delay-between-messages")
    sys.exit(1)

# valid path
if not os.path.exists(sys.argv[1]):
    print(f"File {sys.argv[1]} does not exist.")
    sys.exit(1)

# valid delay
try:
    delay = int(sys.argv[2])
    if delay < 0:
        raise ValueError
except ValueError:
    print(f"Delay {sys.argv[2]} is not a valid integer.")
    sys.exit(1)


kafka_server_bash_command = "kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
bootstrap_server = os.popen(kafka_server_bash_command).read().strip()
bootstrap_server = f"{bootstrap_server}:9094"

file_path = sys.argv[1]
delay = int(sys.argv[2])
topic = "network-traffic"

print(f"Bootstrap servers: {bootstrap_server}")
print(f"Delay between messages: {delay} seconds")
print(f"File: {file_path}")

first_line = True
try:
    producer = KafkaProducer(bootstrap_servers=bootstrap_server)

    while True:
        with open(file_path, 'r') as file:
            for line in file:
                if first_line:
                    first_line = False
                    continue
                message = line.strip()
                producer.send(topic, value=message.encode('utf-8'))
                print(f"Sent: {message}")
                time.sleep(delay)
            break
    producer.flush()
    producer.close()
    print("All messages sent successfully.")
except Exception as e:
    print(f"An error occured: {e}")