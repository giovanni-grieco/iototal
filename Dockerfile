FROM apache/spark:latest

LABEL maintainer="Giovanni Pio Grieco, Emilia Russo"
USER root
RUN pip install numpy
