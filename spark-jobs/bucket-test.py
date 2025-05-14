from pyspark.sql import SparkSession
from pyspark import SparkConf
import os
import datetime

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
    ("spark.hadoop.fs.s3a.fast.upload.buffer", "disk"),  # Use disk buffering for large files
    ("spark.hadoop.fs.s3a.threads.max", "10"),  # Limit the number of threads
    ("spark.hadoop.fs.s3a.connection.maximum", "10"), 
])

def main():
    #Test bucket by saving a file to it
    # Create a Spark session
    date_time = datetime.datetime.now()
    file_name = f"iototal-{date_time.strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    spark = SparkSession.builder \
        .appName("Test Bucket") \
        .config(conf=conf) \
        .getOrCreate()
    # Create a DataFrame with some test data
    data = [("Alice", 1), ("Bob", 2), ("Cathy", 3)]
    df = spark.createDataFrame(data, ["Name", "Id"])
    # Write the DataFrame to a CSV file in the S3 bucket
    df.write.csv(f"s3a://iototal/{file_name}", header=True)
    # Read the CSV file back into a DataFrame
    df_read = spark.read.csv(f"s3a://iototal/{file_name}", header=True)
    # Show the contents of the DataFrame
    df_read.show()
    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    main()
