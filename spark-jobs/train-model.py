from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import StringIndexer
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
        .appName("Random Forest Classifier") \
        .config(conf=conf) \
        .getOrCreate()

    # Load the dataset from S3
    s3_path = "s3a://iototal/Merged01.csv"
    print(f"Loading dataset from {s3_path}")
    data = spark.read.csv(s3_path, header=True, inferSchema=True)

    # Display the schema of the dataset
    data.printSchema()
    
    # Preprocessing: Handle string columns
    label_column_name = "Label"  # Replace with your actual label column name

    # Convert the label column to numeric using StringIndexer
    label_indexer = StringIndexer(inputCol=label_column_name, outputCol="label_indexed", handleInvalid="skip")
    data = label_indexer.fit(data).transform(data)

    # Identify string columns (excluding the label column)
    string_columns = [col for col, dtype in data.dtypes if dtype == "string" and col != label_column_name]

    # Convert string columns to numeric using StringIndexer
    for col in string_columns:
        indexer = StringIndexer(inputCol=col, outputCol=f"{col}_indexed", handleInvalid="skip")
        data = indexer.fit(data).transform(data)

    # Replace original string columns with indexed columns
    feature_columns = [f"{col}_indexed" if col in string_columns else col for col in data.columns if col != label_column_name]

    # Assemble features into a single vector column
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features", handleInvalid="skip")
    data = assembler.transform(data)

    # Split the data into training and test sets
    train_data, test_data = data.randomSplit([0.8, 0.2], seed=42)

    # Train a Random Forest Classifier
    rf = RandomForestClassifier(featuresCol="features", labelCol="label_indexed", numTrees=10, maxBins=150000, maxDepth=5)
    model = rf.fit(train_data)

    # Evaluate the model on the test set
    predictions = model.transform(test_data)
    evaluator = MulticlassClassificationEvaluator(labelCol="label_indexed", predictionCol="prediction", metricName="accuracy")
    accuracy = evaluator.evaluate(predictions)
    print(f"Test Accuracy: {accuracy}")

    # Save the trained model to S3
    model_path = "s3a://iototal/random-forest-model"
    print(f"Saving model to {model_path}")
    model.write().overwrite().save(model_path)

    # Stop the Spark session
    spark.stop()

if __name__ == "__main__":
    main()