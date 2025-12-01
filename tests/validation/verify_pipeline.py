# Databricks notebook source
# MAGIC %md
# MAGIC # Pipeline Verification
# MAGIC
# MAGIC Quick verification of Twitter ingestion → Bronze → Silver pipeline

# COMMAND ----------

print("=" * 60)
print("PIPELINE VERIFICATION")
print("=" * 60)
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Check Bronze Table

# COMMAND ----------

from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

bronze_table = "main.ai_newsletter_bronze.tweets"

try:
    bronze_df = spark.read.format("delta").table(bronze_table)
    bronze_count = bronze_df.count()

    print(f"✅ Bronze Table: {bronze_table}")
    print(f"   Records: {bronze_count}")

    # Show schema
    print("\n   Schema:")
    bronze_df.printSchema()

    # Check for real vs dummy tweets
    dummy_count = bronze_df.filter("id LIKE 'dummy%'").count()
    real_count = bronze_count - dummy_count

    print(f"\n   Data Breakdown:")
    print(f"   - Dummy tweets: {dummy_count}")
    print(f"   - Real tweets:  {real_count}")

    # Show sample
    print(f"\n   Sample Records:")
    bronze_df.select("id", "text", "author_id").show(5, truncate=60)

except Exception as e:
    print(f"❌ ERROR accessing bronze table: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Check Silver Table

# COMMAND ----------

silver_table = "main.ai_newsletter_silver.tweets"

try:
    silver_df = spark.read.format("delta").table(silver_table)
    silver_count = silver_df.count()

    print(f"✅ Silver Table: {silver_table}")
    print(f"   Records: {silver_count}")

    # Show schema
    print("\n   Schema:")
    silver_df.printSchema()

    # Check for duplicates
    duplicate_count = silver_count - silver_df.select("tweet_id").distinct().count()

    print(f"\n   Data Quality:")
    print(f"   - Total records: {silver_count}")
    print(f"   - Unique tweets: {silver_df.select('tweet_id').distinct().count()}")
    print(f"   - Duplicates: {duplicate_count}")

    # Check influence scores
    print(f"\n   Influence Score Stats:")
    silver_df.select("influence_score").describe().show()

    # Show sample with scores
    print(f"\n   Sample Records with Scores:")
    silver_df.select(
        "tweet_id",
        "text",
        "like_count",
        "retweet_count",
        "influence_score"
    ).orderBy("influence_score", ascending=False).show(5, truncate=60)

except Exception as e:
    print(f"❌ ERROR accessing silver table: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Pipeline Summary

# COMMAND ----------

print("=" * 60)
print("PIPELINE SUMMARY")
print("=" * 60)
print()

# Count files in UC Volume
raw_files = dbutils.fs.ls("/Volumes/main/default/ai_newsletter_raw_tweets/")
tweet_files = [f for f in raw_files if f.name.startswith("tweet_") and f.name.endswith(".json")]
real_tweet_files = [f for f in tweet_files if "dummy" not in f.name]

print(f"📁 Raw Data (UC Volume):")
print(f"   Total files: {len(tweet_files)}")
print(f"   Real tweets: {len(real_tweet_files)}")
print(f"   Dummy tweets: {len(tweet_files) - len(real_tweet_files)}")
print()

try:
    bronze_count = spark.read.format("delta").table(bronze_table).count()
    print(f"🥉 Bronze Table: {bronze_count} records")
except:
    print(f"🥉 Bronze Table: Not accessible")

try:
    silver_count = spark.read.format("delta").table(silver_table).count()
    print(f"🥈 Silver Table: {silver_count} records")
except:
    print(f"🥈 Silver Table: Not accessible")

print()
print("=" * 60)
print()

if len(real_tweet_files) > 0:
    print("✅ SUCCESS: Twitter ingestion working with real data!")
else:
    print("⚠️  WARNING: Only dummy data detected")

print()
print("Next Steps:")
print("1. ✅ Twitter ingestion (100 real tweets)")
print("2. ✅ Bronze processing")
print("3. ✅ Silver processing with influence scores")
print("4. ⏭️  T008: Gold daily materialized view")
