from kafka import KafkaProducer

try:
    producer = KafkaProducer(bootstrap_servers='localhost:9092')

    while True:
        message = input("Enter message to send to Kafka topic (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        producer.send('test-topic', value=message.encode('utf-8'))
        print(f"Sent: {message}")
except Exception as e:
    print(f"An error occurred: {e}")
