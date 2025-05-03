# iototal
A Big Data project for Università Roma Tre

## Local execution

### Requirements
[docker](https://docs.docker.com/get-started/get-docker/) or [docker-engine](https://docs.docker.com/get-started/get-docker/)

[minikube](https://minikube.sigs.k8s.io/docs/start/)

[kubectl](https://kubernetes.io/docs/tasks/tools/)

### Run
To start the cluster
```bash
./start-minikube.sh
./start-cluster.sh
```

To stop the cluster
```bash
./stop-cluster.sh
./stop-minikube.sh
```

## Relevant documentation
[Exposing services utilising Minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fdebian+package#Service)

[Kafka on K8](https://learnk8s.io/kafka-ha-kubernetes)

[Submit to Spark on K8](https://apache-spark-on-k8s.github.io/userdocs/running-on-kubernetes.html)


[Interacting with Kafka in Python](https://kafka-python.readthedocs.io/en/master/)