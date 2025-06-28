# Spark Jobs



## iototal-monitor-test.py
This job will consume messages from a Kafka message channel 'network-traffic' and print to stdin the parsing and prediction made by the classification model

## iototal-monitor-final.py
This job will consume messages from a Kafka message channel 'network-traffic' and publish its prediction on another channel 'network-predictions'

## train-model.py
This job will train the model and save it on the s3 bucket
