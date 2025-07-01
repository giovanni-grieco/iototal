# iototal
A Big Data project for Università degli Studi Roma Tre

## Description
iototal is a (near) real-time network traffic classifier that tells the user whether traffic is benign or not

## Logic Architecture
![big-data-system drawio](https://github.com/user-attachments/assets/48f1531f-e171-4e50-bc98-d7bb223b856c)


## Local execution

### Requirements
- [docker](https://docs.docker.com/get-started/get-docker/) or [docker-engine](https://docs.docker.com/engine/install/)
- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/docs/intro/install/)
- [pyspark - for submitting spark jobs](https://spark.apache.org/docs/latest/api/python/getting_started/install.html#using-pypi)
- [gcloud](https://cloud.google.com/sdk/docs/install#linux) and [gke-gcloud-auth-plugin](https://cloud.google.com/sdk/docs/install#linux) (both needed if you want to deploy to GKE otherwise optional if you want to run locally)

#### Install python dependencies (including pyspark)
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

## Secrets
Make sure to create a secrets.yaml file for k8s following this template. As of now it's only used for declaring s3 bucket service secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: minio
  namespace: default
  labels:
    app: iototal
type: Opaque
data:
  accessKey: bWluaW9hZG1pbg== #username (b64 encoding for 'minioadmin')
  secretKey: bWluaW9hZG1pbg== #password (b64 encoding for 'minioadmin')
  endpoint: aHR0cDovL21pbmlvLWhlYWRsZXNzOjkwMDA= #endpoint (b64 encoding for 'http://minio-headless:9000')
```
The secret data have to be in base64. In the example shown above, accessKey is the base64 encoding of 'minioadmin' which is the default minio password.

To create base64 strings you can use a linux program directly in the terminal
```bash
echo -n "some-string-you-want-to-encode" | base64
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
