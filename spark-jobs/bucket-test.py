from pyspark.sql import SparkSession
from pyspark import SparkConf
import os

conf = SparkConf()
conf.setAll([
    ("spark.hadoop.fs.s3a.access.key", os.environ.get("S3_ACCESS_KEY")),
    ("spark.hadoop.fs.s3a.secret.key", os.environ.get("S3_SECRET_KEY")),
    ("spark.hadoop.fs.s3a.endpoint", os.environ.get("S3_BUCKET_ENDPOINT")),
    ("spark.hadoop.fs.s3a.path.style.access", "true"),
    ("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"),
    ("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
])

def main():
    #Test bucket by saving a file to it
    # Create a Spark session

    spark = SparkSession.builder \
        .appName("Test Bucket") \
        .config(conf=conf) \
        .getOrCreate()
    # Create a DataFrame with some test data
    data = [("Alice", 1), ("Bob", 2), ("Cathy", 3)]
    df = spark.createDataFrame(data, ["Name", "Id"])
    # Write the DataFrame to a CSV file in the S3 bucket
    df.write.csv("s3a://iototal/test_data.csv", header=True)
    # Read the CSV file back into a DataFrame
    df_read = spark.read.csv("s3a://iototal/test_data.csv", header=True)
    # Show the contents of the DataFrame
    df_read.show()
    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    main()
