from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.ml.feature import StringIndexer
import os
import json

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
        .appName("Label Mapping Generator") \
        .config(conf=conf) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    
    # Load the dataset from S3
    s3_path = "s3a://iototal/Merged01.csv"
    print(f"Loading dataset from {s3_path}")
    data = spark.read.csv(s3_path, header=True, inferSchema=True)

    # Display the schema of the dataset
    data.printSchema()
    
    # Label column configuration
    label_column_name = "Label"
    
    # Check if the label column exists
    if label_column_name not in data.columns:
        print(f"Error: Column '{label_column_name}' not found in dataset")
        print(f"Available columns: {data.columns}")
        spark.stop()
        return

    # Get unique labels from the dataset
    unique_labels = data.select(label_column_name).distinct().collect()
    print(f"Found {len(unique_labels)} unique labels:")
    for row in unique_labels:
        print(f"  - {row[label_column_name]}")

    # Create StringIndexer to generate the mapping
    label_indexer = StringIndexer(inputCol=label_column_name, outputCol="label_indexed", handleInvalid="skip")
    label_indexer_model = label_indexer.fit(data)
    
    # Get the label mapping (index -> original string value)
    label_mapping = {i: label for i, label in enumerate(label_indexer_model.labels)}
    
    # Also create reverse mapping (original -> index)
    reverse_label_mapping = {label: i for i, label in enumerate(label_indexer_model.labels)}
    
    print("\nLabel mapping (index -> original):")
    for index, original_label in label_mapping.items():
        print(f"  {index} -> {original_label}")
    
    print("\nReverse label mapping (original -> index):")
    for original_label, index in reverse_label_mapping.items():
        print(f"  {original_label} -> {index}")

    # Create comprehensive mapping data
    mapping_data = {
        "label_column": label_column_name,
        "total_labels": len(label_mapping),
        "index_to_label": label_mapping,
        "label_to_index": reverse_label_mapping,
        "generated_timestamp": spark.sql("SELECT current_timestamp()").collect()[0][0].isoformat()
    }

    # Save the mapping to S3 as JSON
    output_path = "s3a://iototal/label-mapping"
    print(f"\nSaving label mapping to {output_path}")
    
    # Convert to DataFrame and save
    mapping_df = spark.createDataFrame([mapping_data])
    mapping_df.coalesce(1).write.format("json").mode("overwrite").save(output_path)
    
    # Also save the StringIndexer model for future use
    indexer_model_path = output_path + "/string_indexer_model"
    print(f"Saving StringIndexer model to {indexer_model_path}")
    label_indexer_model.write().overwrite().save(indexer_model_path)
    
    print("\nLabel mapping generation completed successfully!")
    print(f"- JSON mapping saved to: {output_path}")
    print(f"- StringIndexer model saved to: {indexer_model_path}")

    # Stop the Spark session
    spark.stop()

if __name__ == "__main__":
    main()
