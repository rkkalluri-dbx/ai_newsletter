# Databricks notebook source
"""
Twitter Ingestion Watermark Management
Tracks the last successful ingestion timestamp to avoid re-fetching tweets
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from datetime import datetime, timezone

spark = SparkSession.builder.appName("twitter_watermark").getOrCreate()

# Watermark table configuration
CATALOG = "main"
SCHEMA = "config"
WATERMARK_TABLE = f"{CATALOG}.{SCHEMA}.twitter_ingestion_watermark"

# COMMAND ----------

def create_watermark_table():
    """Create watermark table if it doesn't exist"""

    # Ensure schema exists
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

    if not spark.catalog.tableExists(WATERMARK_TABLE):
        print(f"Creating watermark table: {WATERMARK_TABLE}")

        schema = StructType([
            StructField("job_name", StringType(), False),
            StructField("last_ingestion_time", TimestampType(), False),
            StructField("last_tweet_id", StringType(), True),
            StructField("tweets_fetched", StringType(), True),
            StructField("updated_at", TimestampType(), False)
        ])

        empty_df = spark.createDataFrame([], schema)
        empty_df.write.format("delta").mode("overwrite").saveAsTable(WATERMARK_TABLE)

        print(f"✅ Watermark table created")
    else:
        print(f"✅ Watermark table exists: {WATERMARK_TABLE}")

# COMMAND ----------

def get_last_watermark(job_name="twitter_ingestion"):
    """Get the last ingestion timestamp for resuming"""

    create_watermark_table()

    try:
        watermark_df = spark.read.format("delta").table(WATERMARK_TABLE)
        watermark_row = watermark_df.filter(f"job_name = '{job_name}'").orderBy("updated_at", ascending=False).first()

        if watermark_row:
            last_time = watermark_row['last_ingestion_time']
            last_tweet_id = watermark_row['last_tweet_id']
            print(f"📍 Last watermark: {last_time} (tweet ID: {last_tweet_id})")
            return last_time, last_tweet_id
        else:
            print(f"📍 No previous watermark found - this is the first run")
            return None, None

    except Exception as e:
        print(f"⚠️  Error reading watermark: {e}")
        return None, None

# COMMAND ----------

def update_watermark(job_name, ingestion_time, last_tweet_id, tweets_count):
    """Update the watermark after successful ingestion"""

    from pyspark.sql import Row
    from delta.tables import DeltaTable

    create_watermark_table()

    print(f"💾 Updating watermark: {ingestion_time} (tweet ID: {last_tweet_id}, count: {tweets_count})")

    new_watermark = spark.createDataFrame([
        Row(
            job_name=job_name,
            last_ingestion_time=ingestion_time,
            last_tweet_id=last_tweet_id,
            tweets_fetched=str(tweets_count),
            updated_at=datetime.now(timezone.utc)
        )
    ])

    # Upsert watermark
    delta_table = DeltaTable.forName(spark, WATERMARK_TABLE)

    delta_table.alias("existing") \
        .merge(
            new_watermark.alias("updates"),
            "existing.job_name = updates.job_name"
        ) \
        .whenMatchedUpdateAll() \
        .whenNotMatchedInsertAll() \
        .execute()

    print(f"✅ Watermark updated successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example Usage

# COMMAND ----------

if __name__ == "__main__":
    # Example: Get last watermark
    last_time, last_id = get_last_watermark("twitter_ingestion")

    # Example: Update watermark after ingestion
    # update_watermark(
    #     job_name="twitter_ingestion",
    #     ingestion_time=datetime.now(timezone.utc),
    #     last_tweet_id="1234567890",
    #     tweets_count=250
    # )
