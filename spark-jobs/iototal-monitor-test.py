from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.ml.classification import RandomForestClassificationModel
from pyspark.sql.functions import col, split, trim, from_json, window, count, avg, collect_list, size
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.ml.feature import VectorAssembler
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

# Define CSV schema based on the dataset
def get_csv_schema():
    return StructType([
        StructField("Header_Length", DoubleType(), True),
        StructField("Protocol_Type", IntegerType(), True),
        StructField("Time_To_Live", DoubleType(), True),
        StructField("Rate", DoubleType(), True),
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
        StructField("Tot_sum", IntegerType(), True),
        StructField("Min", IntegerType(), True),
        StructField("Max", IntegerType(), True),
        StructField("AVG", DoubleType(), True),
        StructField("Std", DoubleType(), True),
        StructField("Tot_size", DoubleType(), True),
        StructField("IAT", DoubleType(), True),
        StructField("Number", IntegerType(), True),
        StructField("Variance", DoubleType(), True),
        StructField("Label", StringType(), True)
    ])

def parse_csv_line(line):
    """Parse a CSV line and return structured data"""
    values = line.split(",")
    if len(values) != 40:  # Expected number of columns
        return None
    
    try:
        # Convert values to appropriate types (matching the schema)
        parsed_values = []
        schema = get_csv_schema()
        
        for i, field in enumerate(schema.fields):
            if i < len(values):
                value = values[i].strip()
                if field.dataType == DoubleType():
                    parsed_values.append(float(value) if value else 0.0)
                elif field.dataType == IntegerType():
                    parsed_values.append(int(float(value)) if value else 0)
                else:  # StringType
                    parsed_values.append(value)
            else:
                parsed_values.append(None)
        
        return parsed_values
    except (ValueError, IndexError):
        return None


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
    
    # Parse CSV lines
    schema = get_csv_schema()
    
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
        col("values")[3].cast("double").alias("Rate"),
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
    
    # Prepare features for ML model (exclude Label and kafka_timestamp)
    feature_cols = [col for col in parsed_data.columns if col not in ["kafka_timestamp", "Label"]]
    
    # Create feature vector
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"  # Skip rows with invalid values
    )
    
    # Transform the data to create feature vectors
    vectorized_data = assembler.transform(parsed_data)
    
    # Apply ML model for predictions
    predictions = model.transform(vectorized_data)
    
    # Add window aggregation for analysis (5-minute windows)
    windowed_analysis = predictions \
        .withWatermark("kafka_timestamp", "10 minutes") \
        .groupBy(
            window(col("kafka_timestamp"), "5 minutes", "1 minute"),
            col("prediction")
        ) \
        .agg(
            count("*").alias("count"),
            avg("Rate").alias("avg_rate"),
            collect_list("Label").alias("actual_labels")
        )
    
    # Output predictions to console for monitoring
    prediction_query = predictions.select(
        col("kafka_timestamp"),
        col("prediction"),
        col("Label"),
        col("Rate"),
        col("Protocol_Type")
    ).writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", False) \
        .trigger(processingTime="30 seconds") \
        .start()
    
    # Output windowed analysis
    analysis_query = windowed_analysis.writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", False) \
        .trigger(processingTime="60 seconds") \
        .start()
    
    # Wait for termination
    prediction_query.awaitTermination()
    analysis_query.awaitTermination()



if __name__ == "__main__":
    main()