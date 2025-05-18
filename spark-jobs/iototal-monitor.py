from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import StringIndexer
from pyspark.sql.types import StructType, StructField, DoubleType, IntegerType, StringType
from pyspark.sql.functions import col, from_json
import os

# Spark configuration
conf = SparkConf()
conf.setAll([
    ("spark.hadoop.fs.s3a.access.key", os.environ.get("S3_ACCESS_KEY")),
    ("spark.hadoop.fs.s3a.secret.key", os.environ.get("S3_SECRET_KEY")),
    ("spark.hadoop.fs.s3a.endpoint", os.environ.get("S3_BUCKET_ENDPOINT")),
    ("spark.hadoop.fs.s3a.path.style.access", "true"),
    ("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"),
    ("spark.hadoop.fs.s3a.connection.ssl.enabled", "false"),
    ("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2"),
    ("spark.hadoop.fs.s3a.fast.upload", "true"),
    ("spark.hadoop.fs.s3a.fast.upload.buffer", "disk"),
    ("spark.hadoop.fs.s3a.threads.max", "10"),
    ("spark.hadoop.fs.s3a.connection.maximum", "10"),
    ("spark.ui.showConsoleProgress", "true"),
])


def main():
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Iototal Network Monitor") \
        .config(conf=conf) \
        .getOrCreate()
    # Load model from S3
    model_path = "s3a://iototal/random-forest-model"
    print(f"Loading model from {model_path}")
    model = RandomForestClassifier.load(model_path)
     # Define the schema of the incoming Kafka messages
    schema = StructType([
        StructField("Header_Length", DoubleType(), True),
        StructField("Protocol Type", IntegerType(), True),
        StructField("Time_To_Live", DoubleType(), True),
        StructField("Rate", StringType(), True),
        StructField("fin_flag_number", DoubleType(), True),
        StructField("syn_flag_number", DoubleType(), True),
        StructField("rst_flag_number", DoubleType(), True),
        StructField("psh_flag_number", DoubleType(), True),
        StructField("ack_flag_number", DoubleType(), True),
        StructField("ece_flag_number", DoubleType(), True),
        StructField("cwr_flag_number", DoubleType(), True),
        StructField("ack_count", IntegerType(), True),
        StructField("syn_count", IntegerType(), True),
        StructField("fin_count", IntegerType(), True),
        StructField("rst_count", IntegerType(), True),
        StructField("HTTP", DoubleType(), True),
        StructField("HTTPS", DoubleType(), True),
        StructField("DNS", DoubleType(), True),
        StructField("Telnet", DoubleType(), True),
        StructField("SMTP", DoubleType(), True),
        StructField("SSH", DoubleType(), True),
        StructField("IRC", DoubleType(), True),
        StructField("TCP", DoubleType(), True),
        StructField("UDP", DoubleType(), True),
        StructField("DHCP", DoubleType(), True),
        StructField("ARP", DoubleType(), True),
        StructField("ICMP", DoubleType(), True),
        StructField("IGMP", DoubleType(), True),
        StructField("IPv", DoubleType(), True),
        StructField("LLC", DoubleType(), True),
        StructField("Tot sum", IntegerType(), True),
        StructField("Min", IntegerType(), True),
        StructField("Max", IntegerType(), True),
        StructField("AVG", DoubleType(), True),
        StructField("Std", DoubleType(), True),
        StructField("Tot size", DoubleType(), True),
        StructField("IAT", DoubleType(), True),
        StructField("Number", IntegerType(), True),
        StructField("Variance", DoubleType(), True)
    ])

    # Load the pre-trained Random Forest model
    model_path = "s3a://iototal/random-forest-model"
    print(f"Loading model from {model_path}")
    model = RandomForestClassifier.load(model_path)

    # Read from Kafka topic as a stream
    kafka_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "iototal-kafka-controller-headless:9092") \
        .option("subscribe", "network-traffic") \
        .load()

    # Parse the Kafka messages
    parsed_stream = kafka_stream.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("data")) \
        .select("data.*")

    # Assemble features into a single vector column
    feature_columns = [
        "Header_Length", "Protocol Type", "Time_To_Live", "fin_flag_number", "syn_flag_number",
        "rst_flag_number", "psh_flag_number", "ack_flag_number", "ece_flag_number", "cwr_flag_number",
        "ack_count", "syn_count", "fin_count", "rst_count", "HTTP", "HTTPS", "DNS", "Telnet", "SMTP",
        "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP", "ICMP", "IGMP", "IPv", "LLC", "Tot sum", "Min",
        "Max", "AVG", "Std", "Tot size", "IAT", "Number", "Variance"
    ]
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
    feature_stream = assembler.transform(parsed_stream)

    # Predict the label using the Random Forest model
    predictions = model.transform(feature_stream)

    # Select relevant columns (e.g., features and prediction)
    output_stream = predictions.select("features", "prediction")

    # Write the output to the console in real time
    query = output_stream.writeStream \
        .outputMode("append") \
        .format("console") \
        .start()

    # Wait for the streaming query to finish
    query.awaitTermination()


if __name__ == "__main__":
    main()