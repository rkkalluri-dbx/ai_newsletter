# Databricks notebook source
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, LongType
import time

# --- Configuration ---
raw_data_path = "/Volumes/main/default/ai_newsletter_raw_tweets/"
min_faves_filter = 0  # Changed from 10 to 0 to process all tweets (fresh tweets have low engagement)

# The name of the bronze Delta table. Since UC is enabled, we use a 3-level namespace.
# Explicitly use 'main' catalog for consistency
catalog = "main"
schema = "ai_newsletter_bronze"
bronze_table_name = f"{catalog}.{schema}.tweets"

# Define the schema for the incoming JSON data.
# This is a simplified schema for demonstration purposes.
tweet_schema = StructType([
    StructField("id", StringType(), True),
    StructField("text", StringType(), True),
    StructField("public_metrics", StructType([
        StructField("retweet_count", LongType(), True),
        StructField("reply_count", LongType(), True),
        StructField("like_count", LongType(), True),
        StructField("quote_count", LongType(), True),
    ]), True),
    StructField("author_id", StringType(), True),
    StructField("created_at", StringType(), True)
])

# Create schema if it doesn't exist
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# --- Bronze Layer Processing (T004 & T005) ---
def process_bronze_layer():
    print(f"Starting bronze layer processing. Reading from {raw_data_path} and writing to {bronze_table_name}")

    # Ingest raw JSON data from the landing zone using Auto Loader (T004)
    raw_tweets_df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{raw_data_path}/_schema") # Schema inference and evolution
        .schema(tweet_schema) # Provide schema hint
        .load(raw_data_path)
    )

    # Apply minimum engagement filter (T005)
    filtered_tweets_df = raw_tweets_df.filter(col("public_metrics.like_count") >= min_faves_filter)

    # Write the filtered data to the bronze Delta table as a one-shot micro-batch
    query = (
        filtered_tweets_df.writeStream.format("delta")
        .outputMode("append") # Append new data
        .option("checkpointLocation", f"{raw_data_path}/_checkpoint") # Checkpoint for fault tolerance
        .trigger(once=True) # Process all available data once, then stop
        .toTable(bronze_table_name)
    )

    print(f"Bronze layer processing stream started. Table: {bronze_table_name}")
    query.awaitTermination() # Wait for the micro-batch to complete
    print("Bronze layer processing stream finished or terminated.")

if __name__ == "__main__":
    print("Running ingestion_job.py as a standard Databricks job.")
    process_bronze_layer()
    print(f"Successfully processed raw data and created bronze table: {bronze_table_name}")