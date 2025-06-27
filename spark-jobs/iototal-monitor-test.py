from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.sql.functions import col, split, trim, from_json, window, count, avg, collect_list, size
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.ml.feature import VectorAssembler, StringIndexer
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

    # Load the pre-trained Random Forest model
    model_path = "s3a://iototal/random-forest-model"
    print(f"Loading model from {model_path}")
    model = RandomForestClassificationModel.load(model_path)

    # Read from Kafka topic as a stream
    kafka_stream = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "iototal-kafka-controller-headless:9092") \
        .option("subscribe", "network-traffic") \
        .load()
    
    # Extract the value from Kafka message and convert to string
    raw_data = kafka_stream.select(
        col("timestamp").alias("kafka_timestamp"),
        col("value").cast("string").alias("csv_line")
    )
    
    # Split CSV line into columns and filter valid rows
    split_data = raw_data.select(
        col("kafka_timestamp"),
        split(col("csv_line"), ",").alias("values")
    ).filter(
        # Ensure we have exactly 40 columns
        col("values").getItem(0).isNotNull() & 
        (size(col("values")) == 40)
    )
    
    parsed_data = split_data.select(
        col("kafka_timestamp"),
        # Extract each column with proper type casting
        col("values")[0].cast("double").alias("Header_Length"),
        col("values")[1].cast("int").alias("Protocol_Type"),
        col("values")[2].cast("double").alias("Time_To_Live"),
        col("values")[3].alias("Rate"), # Keep as string initially
        col("values")[4].cast("double").alias("fin_flag_number"),
        col("values")[5].cast("double").alias("syn_flag_number"),
        col("values")[6].cast("double").alias("rst_flag_number"),
        col("values")[7].cast("double").alias("psh_flag_number"),
        col("values")[8].cast("double").alias("ack_flag_number"),
        col("values")[9].cast("double").alias("ece_flag_number"),
        col("values")[10].cast("double").alias("cwr_flag_number"),
        col("values")[11].cast("int").alias("ack_count"),
        col("values")[12].cast("int").alias("syn_count"),
        col("values")[13].cast("int").alias("fin_count"),
        col("values")[14].cast("int").alias("rst_count"),
        col("values")[15].cast("double").alias("HTTP"),
        col("values")[16].cast("double").alias("HTTPS"),
        col("values")[17].cast("double").alias("DNS"),
        col("values")[18].cast("double").alias("Telnet"),
        col("values")[19].cast("double").alias("SMTP"),
        col("values")[20].cast("double").alias("SSH"),
        col("values")[21].cast("double").alias("IRC"),
        col("values")[22].cast("double").alias("TCP"),
        col("values")[23].cast("double").alias("UDP"),
        col("values")[24].cast("double").alias("DHCP"),
        col("values")[25].cast("double").alias("ARP"),
        col("values")[26].cast("double").alias("ICMP"),
        col("values")[27].cast("double").alias("IGMP"),
        col("values")[28].cast("double").alias("IPv"),
        col("values")[29].cast("double").alias("LLC"),
        col("values")[30].cast("int").alias("Tot_sum"),
        col("values")[31].cast("int").alias("Min"),
        col("values")[32].cast("int").alias("Max"),
        col("values")[33].cast("double").alias("AVG"),
        col("values")[34].cast("double").alias("Std"),
        col("values")[35].cast("double").alias("Tot_size"),
        col("values")[36].cast("double").alias("IAT"),
        col("values")[37].cast("int").alias("Number"),
        col("values")[38].cast("double").alias("Variance"),
        col("values")[39].alias("Label")
    )
    
    # For streaming, we need to handle string columns differently
    # Convert Rate to numeric using a simple mapping or hash
    from pyspark.sql.functions import hash
    
    processed_data = parsed_data.select(
        "*",
        hash(col("Rate")).alias("Rate_indexed")
    )
    
    # Prepare features for ML model (exclude kafka_timestamp, Label, and Rate)
    feature_cols = [
        "Header_Length", "Protocol_Type", "Time_To_Live", "Rate_indexed",
        "fin_flag_number", "syn_flag_number", "rst_flag_number", "psh_flag_number",
        "ack_flag_number", "ece_flag_number", "cwr_flag_number", "ack_count",
        "syn_count", "fin_count", "rst_count", "HTTP", "HTTPS", "DNS", "Telnet",
        "SMTP", "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP", "ICMP", "IGMP", "IPv",
        "LLC", "Tot_sum", "Min", "Max", "AVG", "Std", "Tot_size", "IAT", "Number",
        "Variance"
    ]
    
    # Create feature vector
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    
    # Define the streaming query
    def process_batch(batch_df, batch_id):
        if batch_df.count() > 0:
            # Transform the data to create feature vectors
            vectorized_data = assembler.transform(batch_df)
            
            # Apply ML model for predictions
            predictions = model.transform(vectorized_data)
            
            # Show predictions
            predictions.select(
                "kafka_timestamp", "prediction", "Label", "Rate"
            ).show(truncate=False)
    
    # Write stream using foreachBatch
    query = processed_data.writeStream \
        .foreachBatch(process_batch) \
        .trigger(processingTime="30 seconds") \
        .start()
    
    # Wait for termination
    query.awaitTermination()

if __name__ == "__main__":
    main()