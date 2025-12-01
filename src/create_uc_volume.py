# Databricks notebook source
from pyspark.sql import SparkSession

# Initialize Spark Session
spark = SparkSession.builder.appName("create_uc_volume").getOrCreate()

# Define Unity Catalog volume details
catalog_name = "main"
schema_name = "default" # Assuming 'default' schema exists in 'main' catalog
volume_name = "ai_newsletter_raw_tweets"
full_volume_name = f"{catalog_name}.{schema_name}.{volume_name}"

# Create the Unity Catalog volume
try:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {full_volume_name}")
    print(f"Successfully created Unity Catalog Volume: {full_volume_name}")
except Exception as e:
    print(f"Error creating Unity Catalog Volume {full_volume_name}: {e}")
