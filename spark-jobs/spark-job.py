# a test spark job that counts to 100

from pyspark.sql import SparkSession

def main():
    # Create a Spark session
    spark = SparkSession.builder \
        .appName("Count to 100") \
        .getOrCreate()

    # Create a range of numbers from 1 to 100
    numbers = spark.range(1, 101)

    # Count the numbers
    count = numbers.count()

    # Print the count
    print(f"Counted to {count}")

    # Stop the Spark session
    spark.stop()

if __name__ == "__main__":
    main()