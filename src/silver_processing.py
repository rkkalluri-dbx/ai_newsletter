# Databricks notebook source
"""
Silver Layer Processing for AI Newsletter
T007: Deduplication, language filtering, author enrichment, and influence scoring

This job reads from the bronze Delta table, deduplicates tweets, filters for English language,
enriches with author metadata, calculates influence scores, and writes to the silver Delta table.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_date, row_number, lit, coalesce
)
from pyspark.sql.window import Window
from pyspark.sql.types import DoubleType
import pyspark.sql.functions as F

# --- Configuration ---
# Explicitly use 'main' catalog for consistency
catalog = "main"

# Bronze table (source)
bronze_schema = "ai_newsletter_bronze"
bronze_table = f"{catalog}.{bronze_schema}.tweets"

# Silver schema and table (destination)
silver_schema = "ai_newsletter_silver"
silver_table = f"{catalog}.{silver_schema}.tweets"

print(f"Reading from bronze table: {bronze_table}")
print(f"Writing to silver table: {silver_table}")

# --- Create Silver Schema ---
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{silver_schema}")
print(f"Ensured schema exists: {catalog}.{silver_schema}")

# --- Define Influence Score UDF ---
@F.udf(returnType=DoubleType())
def calculate_influence_score(like_count, retweet_count, reply_count, follower_count):
    """
    Calculate influence score based on engagement metrics and follower count.
    Formula: (likes * 2) + (retweets * 3) + (replies * 1) + (follower_count / 1000)

    Args:
        like_count: Number of likes on the tweet
        retweet_count: Number of retweets
        reply_count: Number of replies
        follower_count: Author's follower count

    Returns:
        Influence score as a double
    """
    # Handle None values
    likes = like_count if like_count is not None else 0
    retweets = retweet_count if retweet_count is not None else 0
    replies = reply_count if reply_count is not None else 0
    followers = follower_count if follower_count is not None else 0

    # Calculate weighted score
    score = (likes * 2) + (retweets * 3) + (replies * 1) + (followers / 1000.0)
    return float(score)

# --- Silver Layer Processing ---
def process_silver_layer():
    """
    Main silver layer processing function.

    Steps:
    1. Read from bronze Delta table
    2. Deduplicate by tweet ID (keep most recent)
    3. Filter for English language tweets
    4. Enrich with author metadata (placeholder for now)
    5. Calculate influence score
    6. Write to silver Delta table
    """

    print("Starting silver layer processing...")

    # Step 1: Read from bronze table
    bronze_df = spark.read.format("delta").table(bronze_table)
    print(f"Read {bronze_df.count()} records from bronze table")

    # Step 2: Deduplicate by tweet ID
    # Use window function to keep the most recent record for each tweet_id
    # Order by created_at if available, otherwise just drop duplicates by id
    if "created_at" in bronze_df.columns:
        window_spec = Window.partitionBy("id").orderBy(col("created_at").desc())
        deduplicated_df = (
            bronze_df
            .withColumn("row_num", row_number().over(window_spec))
            .filter(col("row_num") == 1)
            .drop("row_num")
        )
    else:
        # If created_at not available, just drop duplicates by id
        deduplicated_df = bronze_df.dropDuplicates(["id"])

    print(f"After deduplication: {deduplicated_df.count()} unique tweets")

    # Step 3: Filter for English language
    # Note: The bronze table doesn't have a 'lang' field in the current schema
    # We'll add a placeholder filter that can be enhanced when language data is available
    # For now, we'll keep all tweets and add a note
    print("Note: Language filtering requires 'lang' field in bronze table schema")
    print("Keeping all tweets for now. To add language filtering:")
    print("  1. Update twitter_ingestion_script.py to include 'lang' field")
    print("  2. Update bronze schema to include language")
    print("  3. Uncomment: filtered_df = deduplicated_df.filter(col('lang') == 'en')")

    filtered_df = deduplicated_df  # Placeholder until lang field is available

    # Step 4: Enrich with author metadata
    # Current bronze schema has: id, text, public_metrics (retweet_count, reply_count, like_count, quote_count), author_id
    # We'll extract the metrics and add placeholders for author enrichment

    # Build select list dynamically based on available columns
    select_list = [
        col("id").alias("tweet_id"),
        col("text"),
        col("author_id"),
        # Placeholder for author name and verification status
        # In a real implementation, join with a users/authors dimension table
        lit("").alias("author_name"),  # TODO: Join with author metadata
        lit(0).cast("long").alias("follower_count"),  # TODO: Get from author metadata
        lit(False).alias("verified"),  # TODO: Get from author metadata
    ]

    # Use created_at from bronze if available, otherwise use current timestamp
    if "created_at" in filtered_df.columns:
        select_list.append(col("created_at"))
    else:
        select_list.append(current_timestamp().alias("created_at"))

    select_list.extend([
        col("public_metrics.like_count").alias("like_count"),
        col("public_metrics.retweet_count").alias("retweet_count"),
        col("public_metrics.reply_count").alias("reply_count"),
        col("public_metrics.quote_count").alias("quote_count")
    ])

    enriched_df = filtered_df.select(*select_list)

    print("Added author enrichment placeholders")
    print("Note: To fully implement author enrichment:")
    print("  1. Create an authors dimension table from Twitter API user data")
    print("  2. Join silver processing with authors table on author_id")
    print("  3. Populate author_name, follower_count, and verified fields")

    # Step 5: Calculate influence score
    scored_df = enriched_df.withColumn(
        "influence_score",
        calculate_influence_score(
            col("like_count"),
            col("retweet_count"),
            col("reply_count"),
            col("follower_count")
        )
    )

    # Add processing timestamp
    final_df = scored_df.withColumn("processed_at", current_timestamp())

    # Reorder columns to match schema specification
    silver_df = final_df.select(
        "tweet_id",
        "text",
        "author_id",
        "author_name",
        "follower_count",
        "verified",
        "created_at",
        "like_count",
        "retweet_count",
        "reply_count",
        "influence_score",
        "processed_at"
    )

    print(f"Calculated influence scores for {silver_df.count()} tweets")

    # Step 6: Write to silver Delta table
    # Use merge to handle updates (in case we reprocess data)
    print(f"Writing to silver table: {silver_table}")

    silver_df.write.format("delta").mode("overwrite").option(
        "mergeSchema", "true"
    ).saveAsTable(silver_table)

    print(f"Successfully wrote to silver table: {silver_table}")

    # Show sample data
    print("\nSample silver table data (first 5 rows):")
    spark.read.format("delta").table(silver_table).show(5, truncate=False)

    # Show statistics
    stats_df = spark.sql(f"""
        SELECT
            COUNT(*) as total_tweets,
            COUNT(DISTINCT tweet_id) as unique_tweets,
            AVG(influence_score) as avg_influence_score,
            MAX(influence_score) as max_influence_score,
            MIN(influence_score) as min_influence_score
        FROM {silver_table}
    """)

    print("\nSilver table statistics:")
    stats_df.show()

    return silver_df

# --- Main Execution ---
if __name__ == "__main__":
    print("=" * 80)
    print("T007: Silver Layer Processing - Deduplication, Enrichment & Influence Scoring")
    print("=" * 80)

    try:
        result_df = process_silver_layer()
        print("\n✅ Silver layer processing completed successfully!")
        print(f"Silver table location: {silver_table}")

    except Exception as e:
        print(f"\n❌ Error during silver layer processing: {str(e)}")
        raise

    print("=" * 80)
