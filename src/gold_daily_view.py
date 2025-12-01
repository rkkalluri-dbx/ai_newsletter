# Databricks notebook source
"""
Gold Layer - Daily Top Candidates View
T008: Daily materialized view with top 100 tweets per day by influence score

This job creates a daily snapshot of the top 100 tweets based on influence scores.
The view is partitioned by date for efficient querying and serves as input for the LLM agent.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_date, row_number, rank, dense_rank
)
from pyspark.sql.window import Window

# COMMAND ----------

# Initialize Spark session
spark = SparkSession.builder.appName("gold_daily_view").getOrCreate()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Table names
silver_table = "main.ai_newsletter_silver.tweets"
gold_schema = "ai_newsletter_gold"
gold_table = f"main.{gold_schema}.daily_top_candidates"

# Create gold schema if it doesn't exist
spark.sql(f"CREATE SCHEMA IF NOT EXISTS main.{gold_schema}")

print(f"Source: {silver_table}")
print(f"Target: {gold_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Silver Table

# COMMAND ----------

# Read silver table
try:
    silver_df = spark.read.format("delta").table(silver_table)
    record_count = silver_df.count()
    print(f"Total records in silver table: {record_count}")

    if record_count == 0:
        print("⚠️  Silver table is empty. Cannot create gold view.")
        print("Run bronze and silver processing jobs first.")
        dbutils.notebook.exit("Silver table is empty")

    silver_df.printSchema()
except Exception as e:
    print(f"❌ Error reading silver table: {e}")
    dbutils.notebook.exit(f"Failed to read silver table: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Extract Date and Filter Current Day

# COMMAND ----------

# Add date column from created_at timestamp
# Filter for tweets from today (or last 24 hours if created_at is recent)
daily_df = (
    silver_df
    .withColumn("tweet_date", to_date(col("created_at")))
    .filter(col("tweet_date") == to_date(current_timestamp()))
)

print(f"Tweets from today: {daily_df.count()}")

# If no tweets from today, take most recent day available
if daily_df.count() == 0:
    print("No tweets from today, using most recent date available...")

    # Get the most recent date
    max_date_row = silver_df.selectExpr("to_date(max(created_at)) as max_date").collect()[0]
    max_date = max_date_row.max_date

    print(f"Using date: {max_date}")

    daily_df = (
        silver_df
        .withColumn("tweet_date", to_date(col("created_at")))
        .filter(col("tweet_date") == max_date)
    )

    print(f"Tweets from {max_date}: {daily_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Rank by Influence Score

# COMMAND ----------

# Create window spec to rank tweets by influence score
window_spec = Window.partitionBy("tweet_date").orderBy(col("influence_score").desc())

# Add rank and row_number
ranked_df = (
    daily_df
    .withColumn("daily_rank", row_number().over(window_spec))
    .withColumn("influence_rank", rank().over(window_spec))
)

print("Ranked tweets sample:")
ranked_df.select("tweet_id", "text", "influence_score", "daily_rank").show(10, truncate=60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Select Top 100 Candidates

# COMMAND ----------

# Select top 100 tweets per day
top_candidates_df = ranked_df.filter(col("daily_rank") <= 100)

print(f"Top 100 candidates selected: {top_candidates_df.count()}")

# Add processing timestamp
final_df = top_candidates_df.withColumn("processed_at", current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Gold Table

# COMMAND ----------

# Write to gold table (overwrite for daily refresh)
print(f"Writing to {gold_table}...")

final_df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .partitionBy("tweet_date") \
    .saveAsTable(gold_table)

print(f"✅ Successfully wrote {final_df.count()} records to {gold_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify the gold table
gold_verify_df = spark.read.format("delta").table(gold_table)

print("\n" + "=" * 60)
print("GOLD TABLE VERIFICATION")
print("=" * 60)
print(f"Table: {gold_table}")
print(f"Total records: {gold_verify_df.count()}")
print(f"Partitions: {gold_verify_df.select('tweet_date').distinct().count()} day(s)")

print("\nSchema:")
gold_verify_df.printSchema()

print("\nTop 10 tweets by influence score:")
gold_verify_df.orderBy("daily_rank") \
    .select("daily_rank", "tweet_id", "text", "influence_score", "like_count", "retweet_count") \
    .show(10, truncate=60)

print("\nInfluence score distribution (top 100):")
gold_verify_df.select("influence_score").describe().show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("T008: GOLD DAILY VIEW - COMPLETE")
print("=" * 60)
print(f"✅ Created table: {gold_table}")
print(f"✅ Top 100 candidates per day")
print(f"✅ Ranked by influence score")
print(f"✅ Partitioned by tweet_date")
print(f"✅ Ready for LLM agent consumption")
print("=" * 60)
