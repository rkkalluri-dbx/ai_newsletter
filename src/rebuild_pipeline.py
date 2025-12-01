# Databricks notebook source
"""
Comprehensive Pipeline Rebuild Script
This script rebuilds the entire AI Newsletter data pipeline from scratch.

It will:
1. Verify raw data exists
2. Create all required schemas
3. Process bronze layer (raw JSON → bronze Delta table)
4. Process silver layer (deduplication, enrichment, influence scoring)
5. Process gold layer (daily top 100, weekly top 200)
6. Verify all tables exist with data

Run this notebook to fix pipeline issues or rebuild from scratch.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_date, row_number, lit, coalesce,
    from_json, date_sub, current_date, sum as _sum, count as _count
)
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType
import pyspark.sql.functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC # Configuration

# COMMAND ----------

# Initialize Spark
spark = SparkSession.builder.appName("rebuild_pipeline").getOrCreate()

# Catalog and schema configuration
CATALOG = "main"
RAW_DATA_PATH = "/Volumes/main/default/ai_newsletter_raw_tweets/"

# Schema names
CONFIG_SCHEMA = f"{CATALOG}.config"
BRONZE_SCHEMA = f"{CATALOG}.ai_newsletter_bronze"
SILVER_SCHEMA = f"{CATALOG}.ai_newsletter_silver"
GOLD_SCHEMA = f"{CATALOG}.ai_newsletter_gold"

# Table names
CONFIG_TABLE = f"{CONFIG_SCHEMA}.search_terms"
BRONZE_TABLE = f"{BRONZE_SCHEMA}.tweets"
SILVER_TABLE = f"{SILVER_SCHEMA}.tweets"
GOLD_DAILY_TABLE = f"{GOLD_SCHEMA}.daily_top_candidates"
GOLD_WEEKLY_TABLE = f"{GOLD_SCHEMA}.weekly_top_stories"
GOLD_AUTHORS_TABLE = f"{GOLD_SCHEMA}.weekly_trending_authors"

# Configuration
MIN_FAVES_FILTER = 10

print("=" * 70)
print("COMPREHENSIVE PIPELINE REBUILD")
print("=" * 70)
print(f"\nCatalog: {CATALOG}")
print(f"Raw Data: {RAW_DATA_PATH}")
print(f"\nSchemas to create:")
print(f"  - {CONFIG_SCHEMA}")
print(f"  - {BRONZE_SCHEMA}")
print(f"  - {SILVER_SCHEMA}")
print(f"  - {GOLD_SCHEMA}")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 1: Verify Raw Data

# COMMAND ----------

print("\n[STEP 1] Verifying raw data...")

try:
    # List files in raw data path
    files = dbutils.fs.ls(RAW_DATA_PATH)
    json_files = [f for f in files if f.path.endswith('.json')]

    print(f"✅ Raw data path exists: {RAW_DATA_PATH}")
    print(f"✅ Found {len(json_files)} JSON files")

    if len(json_files) == 0:
        print("⚠️  WARNING: No JSON files found. Run Twitter ingestion job first!")
        dbutils.notebook.exit("No raw data found. Please run Twitter ingestion job.")

    # Show sample files
    print(f"\nSample files (first 5):")
    for f in json_files[:5]:
        print(f"  - {f.name}")

except Exception as e:
    print(f"❌ ERROR: Cannot access raw data - {e}")
    dbutils.notebook.exit(f"Raw data path error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 2: Create All Schemas

# COMMAND ----------

print("\n[STEP 2] Creating schemas...")

schemas_to_create = [
    (CONFIG_SCHEMA, "Configuration tables (search terms)"),
    (BRONZE_SCHEMA, "Bronze layer (raw ingestion)"),
    (SILVER_SCHEMA, "Silver layer (cleaned, enriched)"),
    (GOLD_SCHEMA, "Gold layer (aggregated views)")
]

for schema, description in schemas_to_create:
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        print(f"✅ Created/verified schema: {schema}")
        print(f"   Description: {description}")
    except Exception as e:
        print(f"❌ ERROR creating schema {schema}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 3: Process Bronze Layer

# COMMAND ----------

print("\n[STEP 3] Processing bronze layer...")

# Define tweet schema
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

try:
    print(f"Reading from: {RAW_DATA_PATH}")
    print(f"Writing to: {BRONZE_TABLE}")

    # Read raw JSON with Auto Loader
    raw_tweets_df = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{RAW_DATA_PATH}/_schema")
        .schema(tweet_schema)
        .load(RAW_DATA_PATH)
    )

    # Apply minimum engagement filter
    filtered_tweets_df = raw_tweets_df.filter(col("public_metrics.like_count") >= MIN_FAVES_FILTER)

    # Write to bronze table
    query = (
        filtered_tweets_df.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{RAW_DATA_PATH}/_checkpoint")
        .trigger(once=True)
        .toTable(BRONZE_TABLE)
    )

    print("✅ Bronze stream started...")
    query.awaitTermination()
    print("✅ Bronze processing complete!")

    # Verify bronze table
    bronze_df = spark.read.format("delta").table(BRONZE_TABLE)
    bronze_count = bronze_df.count()
    print(f"✅ Bronze table created: {bronze_count} records")

except Exception as e:
    print(f"❌ ERROR in bronze processing: {e}")
    print("Continuing to next step...")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 4: Process Silver Layer

# COMMAND ----------

print("\n[STEP 4] Processing silver layer...")

# Define Influence Score UDF
@F.udf(returnType=DoubleType())
def calculate_influence_score(like_count, retweet_count, reply_count, follower_count):
    likes = like_count if like_count is not None else 0
    retweets = retweet_count if retweet_count is not None else 0
    replies = reply_count if reply_count is not None else 0
    followers = follower_count if follower_count is not None else 0

    score = (likes * 2) + (retweets * 3) + (replies * 1) + (followers / 1000.0)
    return float(score)

try:
    # Read from bronze table
    bronze_df = spark.read.format("delta").table(BRONZE_TABLE)
    bronze_count = bronze_df.count()

    if bronze_count == 0:
        print("⚠️  Bronze table is empty. Cannot process silver layer.")
    else:
        print(f"Reading {bronze_count} records from bronze table...")

        # Flatten the structure
        flattened_df = bronze_df.select(
            col("id").alias("tweet_id"),
            col("text"),
            col("author_id"),
            col("created_at"),
            col("public_metrics.like_count").alias("like_count"),
            col("public_metrics.retweet_count").alias("retweet_count"),
            col("public_metrics.reply_count").alias("reply_count"),
            col("public_metrics.quote_count").alias("quote_count")
        )

        # Deduplicate by tweet_id (keep most recent)
        window_spec = Window.partitionBy("tweet_id").orderBy(col("created_at").desc())
        deduped_df = (
            flattened_df
            .withColumn("row_num", row_number().over(window_spec))
            .filter(col("row_num") == 1)
            .drop("row_num")
        )

        # Add author metadata (placeholder - using defaults)
        enriched_df = (
            deduped_df
            .withColumn("author_name", lit("Unknown"))
            .withColumn("author_username", lit("unknown"))
            .withColumn("follower_count", lit(1000))
            .withColumn("lang", lit("en"))
        )

        # Calculate influence score
        scored_df = enriched_df.withColumn(
            "influence_score",
            calculate_influence_score(
                col("like_count"),
                col("retweet_count"),
                col("reply_count"),
                col("follower_count")
            )
        )

        # Add metadata
        final_df = scored_df.withColumn("processed_at", current_timestamp())

        # Write to silver table
        final_df.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(SILVER_TABLE)

        silver_count = final_df.count()
        print(f"✅ Silver table created: {silver_count} records")

        # Show sample
        print("\nSample records:")
        final_df.select("tweet_id", "text", "influence_score", "like_count").show(5, truncate=60)

except Exception as e:
    print(f"❌ ERROR in silver processing: {e}")
    print("Continuing to next step...")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 5: Process Gold Daily Layer

# COMMAND ----------

print("\n[STEP 5] Processing gold daily layer...")

try:
    # Read from silver table
    silver_df = spark.read.format("delta").table(SILVER_TABLE)
    silver_count = silver_df.count()

    if silver_count == 0:
        print("⚠️  Silver table is empty. Cannot process gold daily layer.")
    else:
        print(f"Reading {silver_count} records from silver table...")

        # Add date column
        daily_df = silver_df.withColumn("tweet_date", to_date(col("created_at")))

        # Get most recent date
        max_date_row = silver_df.selectExpr("to_date(max(created_at)) as max_date").collect()[0]
        max_date = max_date_row.max_date

        # Filter for most recent date
        daily_filtered = daily_df.filter(col("tweet_date") == max_date)

        # Rank by influence score
        window_spec = Window.partitionBy("tweet_date").orderBy(col("influence_score").desc())
        ranked_df = (
            daily_filtered
            .withColumn("daily_rank", row_number().over(window_spec))
            .withColumn("influence_rank", F.rank().over(window_spec))
        )

        # Select top 100
        top_100 = ranked_df.filter(col("daily_rank") <= 100) \
            .withColumn("processed_at", current_timestamp())

        # Write to gold daily table
        top_100.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .partitionBy("tweet_date") \
            .saveAsTable(GOLD_DAILY_TABLE)

        daily_count = top_100.count()
        print(f"✅ Gold daily table created: {daily_count} records for {max_date}")

        # Show sample
        print("\nTop 5 daily tweets:")
        top_100.select("daily_rank", "text", "influence_score").show(5, truncate=60)

except Exception as e:
    print(f"❌ ERROR in gold daily processing: {e}")
    print("Continuing to next step...")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 6: Process Gold Weekly Layer

# COMMAND ----------

print("\n[STEP 6] Processing gold weekly layer...")

try:
    # Read from silver table
    silver_df = spark.read.format("delta").table(SILVER_TABLE)
    silver_count = silver_df.count()

    if silver_count == 0:
        print("⚠️  Silver table is empty. Cannot process gold weekly layer.")
    else:
        print(f"Reading {silver_count} records from silver table...")

        # Date range: last 7 days
        days_back = 7
        end_date = current_date()
        start_date = date_sub(end_date, days_back)

        # Filter for last 7 days
        weekly_df = (
            silver_df
            .withColumn("tweet_date", to_date(col("created_at")))
            .filter(col("tweet_date") >= start_date)
            .filter(col("tweet_date") <= end_date)
        )

        weekly_count = weekly_df.count()

        # If no data in last 7 days, use all available
        if weekly_count == 0:
            print("No data in last 7 days, using all available data...")
            weekly_df = silver_df.withColumn("tweet_date", to_date(col("created_at")))

        # Rank by influence score
        window_spec = Window.orderBy(col("influence_score").desc())
        weekly_ranked = weekly_df.withColumn("weekly_rank", row_number().over(window_spec))

        # Select top 200
        top_200 = weekly_ranked.filter(col("weekly_rank") <= 200) \
            .withColumn("week_start_date", date_sub(current_date(), days_back)) \
            .withColumn("week_end_date", current_date()) \
            .withColumn("processed_at", current_timestamp())

        # Write to gold weekly table
        top_200.write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .partitionBy("week_start_date") \
            .saveAsTable(GOLD_WEEKLY_TABLE)

        result_count = top_200.count()
        print(f"✅ Gold weekly table created: {result_count} records")

        # Show sample
        print("\nTop 5 weekly tweets:")
        top_200.select("weekly_rank", "text", "influence_score").show(5, truncate=60)

        # Create trending authors table
        print("\nCreating trending authors table...")
        author_stats = (
            top_200
            .groupBy("author_id", "author_name")
            .agg(
                _count("tweet_id").alias("tweet_count"),
                _sum("like_count").alias("total_likes"),
                _sum("retweet_count").alias("total_retweets"),
                _sum("influence_score").alias("total_influence")
            )
            .orderBy(col("total_influence").desc())
            .limit(20)
        )

        author_stats.withColumn("week_start_date", date_sub(current_date(), days_back)) \
            .withColumn("week_end_date", current_date()) \
            .withColumn("processed_at", current_timestamp()) \
            .write.format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(GOLD_AUTHORS_TABLE)

        author_count = author_stats.count()
        print(f"✅ Trending authors table created: {author_count} records")

except Exception as e:
    print(f"❌ ERROR in gold weekly processing: {e}")
    print("Continuing to verification...")

# COMMAND ----------

# MAGIC %md
# MAGIC # Step 7: Final Verification

# COMMAND ----------

print("\n[STEP 7] Final verification...")
print("\n" + "=" * 70)
print("PIPELINE REBUILD COMPLETE")
print("=" * 70)

# Check all tables
tables_to_check = [
    (CONFIG_TABLE, "Config: Search Terms"),
    (BRONZE_TABLE, "Bronze: Raw Tweets"),
    (SILVER_TABLE, "Silver: Enriched Tweets"),
    (GOLD_DAILY_TABLE, "Gold: Daily Top 100"),
    (GOLD_WEEKLY_TABLE, "Gold: Weekly Top 200"),
    (GOLD_AUTHORS_TABLE, "Gold: Trending Authors")
]

results = []

for table_name, description in tables_to_check:
    try:
        df = spark.read.format("delta").table(table_name)
        count = df.count()
        status = "✅" if count > 0 else "⚠️ "
        results.append((status, description, count))
        print(f"{status} {description}: {count} records")
    except Exception as e:
        results.append(("❌", description, 0))
        print(f"❌ {description}: NOT FOUND")

print("=" * 70)

# Summary
success_count = len([r for r in results if r[0] == "✅"])
total_count = len(results)

print(f"\nTables created: {success_count}/{total_count}")

if success_count == total_count:
    print("\n🎉 SUCCESS! All tables created and populated.")
    print("\nNext steps:")
    print("  1. View tables in Catalog: main → ai_newsletter_*")
    print("  2. Run validation: ./tests/validation/validate_gold_layer.sh")
    print("  3. Start Epic 3: LLM Summarization Agent")
elif success_count >= 3:
    print("\n⚠️  PARTIAL SUCCESS! Some tables created.")
    print("Check errors above for details on missing tables.")
else:
    print("\n❌ PIPELINE REBUILD FAILED")
    print("Review errors above and check:")
    print("  1. Raw data exists in UC Volume")
    print("  2. Unity Catalog permissions")
    print("  3. Cluster configuration")

print("=" * 70)
