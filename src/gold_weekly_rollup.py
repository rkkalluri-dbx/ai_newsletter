# Databricks notebook source
"""
Gold Layer - Weekly Top Stories Rollup
T009: Weekly rollup view aggregating last 7 days of top candidates

This job creates a weekly aggregation of the top performing tweets over the last 7 days.
It includes engagement metrics, trending topics, and top authors for the weekly newsletter.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_date, current_date, date_sub,
    row_number, sum as _sum, avg as _avg, count as _count, max as _max,
    collect_list, array_distinct, size, explode, split, lower, trim
)
from pyspark.sql.window import Window

# COMMAND ----------

# Initialize Spark session
spark = SparkSession.builder.appName("gold_weekly_rollup").getOrCreate()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Table names
silver_table = "main.ai_newsletter_silver.tweets"
gold_schema = "ai_newsletter_gold"
gold_table = f"main.{gold_schema}.weekly_top_stories"

# Create gold schema if it doesn't exist
spark.sql(f"CREATE SCHEMA IF NOT EXISTS main.{gold_schema}")

# Weekly window: last 7 days
days_back = 7

print(f"Source: {silver_table}")
print(f"Target: {gold_table}")
print(f"Time window: Last {days_back} days")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Silver Table - Last 7 Days

# COMMAND ----------

# Read silver table
try:
    silver_df = spark.read.format("delta").table(silver_table)
    record_count = silver_df.count()
    print(f"Total records in silver table: {record_count}")

    if record_count == 0:
        print("⚠️  Silver table is empty. Cannot create weekly rollup.")
        print("Run bronze and silver processing jobs first.")
        dbutils.notebook.exit("Silver table is empty")

    # Calculate date range
    end_date = current_date()
    start_date = date_sub(end_date, days_back)

    print(f"Date range: {start_date} to {end_date}")

except Exception as e:
    print(f"❌ Error reading silver table: {e}")
    dbutils.notebook.exit(f"Failed to read silver table: {e}")

# Filter for last 7 days
weekly_df = (
    silver_df
    .withColumn("tweet_date", to_date(col("created_at")))
    .filter(col("tweet_date") >= start_date)
    .filter(col("tweet_date") <= end_date)
)

total_tweets = weekly_df.count()
print(f"Tweets in last {days_back} days: {total_tweets}")

if total_tweets == 0:
    print(f"⚠️  No tweets found in last {days_back} days")
    print("Using all available tweets instead...")
    weekly_df = silver_df.withColumn("tweet_date", to_date(col("created_at")))
    print(f"Total tweets available: {weekly_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Rank Weekly Top Tweets

# COMMAND ----------

# Rank all tweets by influence score across the entire week
window_spec = Window.orderBy(col("influence_score").desc())

weekly_ranked_df = (
    weekly_df
    .withColumn("weekly_rank", row_number().over(window_spec))
)

# Take top 200 for weekly consideration (more than daily for variety)
top_weekly_tweets = weekly_ranked_df.filter(col("weekly_rank") <= 200)

print(f"Top 200 weekly tweets selected: {top_weekly_tweets.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculate Weekly Engagement Metrics

# COMMAND ----------

# Aggregate weekly engagement stats
weekly_stats = top_weekly_tweets.agg(
    _sum("like_count").alias("total_likes"),
    _sum("retweet_count").alias("total_retweets"),
    _sum("reply_count").alias("total_replies"),
    _avg("influence_score").alias("avg_influence_score"),
    _max("influence_score").alias("max_influence_score"),
    _count("tweet_id").alias("total_tweets")
)

print("\nWeekly Engagement Metrics:")
weekly_stats.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Identify Trending Authors

# COMMAND ----------

# Find top authors by total engagement
author_stats = (
    top_weekly_tweets
    .groupBy("author_id", "author_name")
    .agg(
        _count("tweet_id").alias("tweet_count"),
        _sum("like_count").alias("total_likes"),
        _sum("retweet_count").alias("total_retweets"),
        _sum("influence_score").alias("total_influence")
    )
    .orderBy(col("total_influence").desc())
)

print("\nTop 10 Authors by Influence:")
author_stats.show(10, truncate=False)

# Get list of trending authors (top 20)
trending_authors_df = author_stats.limit(20).select(
    col("author_id"),
    col("author_name"),
    col("tweet_count"),
    col("total_influence")
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Extract Topics/Keywords (Simple)

# COMMAND ----------

# Extract common words as simple topic indicators
# This is a basic implementation - could be enhanced with NLP/topic modeling

# Split text into words, filter common words
from pyspark.sql.functions import regexp_replace, length

# Simple keyword extraction (words > 5 chars, exclude common words)
keywords_df = (
    top_weekly_tweets
    .withColumn("text_clean", lower(regexp_replace(col("text"), "[^a-zA-Z\\s]", "")))
    .withColumn("words", split(col("text_clean"), "\\s+"))
    .select("tweet_id", explode("words").alias("word"))
    .filter(length(col("word")) > 5)
    .filter(~col("word").isin(["the", "and", "for", "with", "this", "that", "from", "have", "been", "were", "which", "their", "there", "about", "would", "could", "should"]))
    .groupBy("word")
    .agg(_count("*").alias("frequency"))
    .orderBy(col("frequency").desc())
    .limit(50)
)

print("\nTop Keywords (potential topics):")
keywords_df.show(20, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Weekly Summary View

# COMMAND ----------

# Add metadata to top weekly tweets
final_weekly_df = (
    top_weekly_tweets
    .withColumn("week_start_date", date_sub(current_date(), days_back))
    .withColumn("week_end_date", current_date())
    .withColumn("processed_at", current_timestamp())
    .select(
        "tweet_id",
        "text",
        "author_id",
        "author_name",
        "created_at",
        "tweet_date",
        "like_count",
        "retweet_count",
        "reply_count",
        "follower_count",
        "influence_score",
        "weekly_rank",
        "week_start_date",
        "week_end_date",
        "processed_at"
    )
)

print(f"\nFinal weekly rollup: {final_weekly_df.count()} tweets")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Gold Table

# COMMAND ----------

# Write to gold table (overwrite for weekly refresh)
print(f"Writing to {gold_table}...")

final_weekly_df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .partitionBy("week_start_date") \
    .saveAsTable(gold_table)

print(f"✅ Successfully wrote {final_weekly_df.count()} records to {gold_table}")

# Write trending authors as a separate table
trending_authors_table = f"main.{gold_schema}.weekly_trending_authors"

trending_authors_df.withColumn("week_start_date", date_sub(current_date(), days_back)) \
    .withColumn("week_end_date", current_date()) \
    .withColumn("processed_at", current_timestamp()) \
    .write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(trending_authors_table)

print(f"✅ Also created: {trending_authors_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

# Verify the gold table
gold_verify_df = spark.read.format("delta").table(gold_table)

print("\n" + "=" * 60)
print("GOLD WEEKLY ROLLUP VERIFICATION")
print("=" * 60)
print(f"Table: {gold_table}")
print(f"Total records: {gold_verify_df.count()}")
print(f"Date range: {days_back} days")

print("\nSchema:")
gold_verify_df.printSchema()

print("\nTop 10 tweets by weekly rank:")
gold_verify_df.orderBy("weekly_rank") \
    .select("weekly_rank", "tweet_id", "text", "influence_score", "author_name") \
    .show(10, truncate=60)

print("\nWeekly distribution:")
gold_verify_df.groupBy("tweet_date").count().orderBy("tweet_date").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("T009: GOLD WEEKLY ROLLUP - COMPLETE")
print("=" * 60)
print(f"✅ Created table: {gold_table}")
print(f"✅ Top 200 tweets from last {days_back} days")
print(f"✅ Ranked by influence score")
print(f"✅ Trending authors identified: {trending_authors_table}")
print(f"✅ Partitioned by week_start_date")
print(f"✅ Ready for weekly newsletter generation")
print("=" * 60)
