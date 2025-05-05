from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
import time

def main():
    # Create a Spark session
    spark = SparkSession.builder \
        .appName("Kafka Test Job") \
        .getOrCreate()

    # Read from Kafka topic as a stream
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "iototal-kafka-controller-headless:9092") \
        .option("subscribe", "test-topic") \
        .load()
    
    # Parse the data
    parsed_df = df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    
    # Write the output to console (for testing)
    query = parsed_df \
        .writeStream \
        .outputMode("append") \
        .format("console") \
        .start()
    
    # Run for 60 seconds then exit
    query.awaitTermination(180)
    
    # Gracefully stop the query and spark session
    query.stop()
    spark.stop()

if __name__ == "__main__":
    main()