# iototal
A Big Data project for Università Roma Tre

## Local execution

### Requirements
- [docker](https://docs.docker.com/get-started/get-docker/) or [docker-engine](https://docs.docker.com/engine/install/)
- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/docs/intro/install/)
- [pyspark - for submitting spark jobs](https://spark.apache.org/docs/latest/api/python/getting_started/install.html#using-pypi)

#### Install pyspark
It's suggested to create a venv in which to install pyspark:
```bash
python -m venv .venv
```
Activate the environment:
```bash
source .venv/bin/activate
```
And finally install the dependencies:
```bash
pip install -r requirements.txt
```


### Run
#### To start the cluster
```bash
./start-minikube.sh #will start a local k8s cluster
./start-cluster.sh  #will start the needed services
```

#### To submit a spark job
```bash
./submit-spark-job.sh path/to/job
```

#### To stop the cluster
```bash
./stop-cluster.sh
./stop-minikube.sh
```

## Relevant documentation
[Exposing services utilising Minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fdebian+package#Service)

[Kafka on K8 (general usage and understanding)](https://learnk8s.io/kafka-ha-kubernetes)

[Bitnami Kafka specific documentation](https://github.com/bitnami/charts/tree/main/bitnami/kafka)

[Interacting with Kafka in Python (Not from inside a Spark job)](https://kafka-python.readthedocs.io/en/master/)

[Submit to Spark on K8](https://spark.apache.org/docs/latest/running-on-kubernetes.html#submitting-applications-to-kubernetes)

[Spark Streaming - Submitting Spark Job that interact with Kafka](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)


## Dataset

[IOTDataset](http://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/Dataset/)