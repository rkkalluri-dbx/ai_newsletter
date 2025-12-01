# Databricks notebook source
"""
Configuration Data Seeding Script
Seeds the config.search_terms table with initial search terms for Twitter ingestion.

This script is idempotent - it can be run multiple times safely.
It will create the schema and table if they don't exist, and upsert search terms.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, TimestampType
from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC # Configuration Data Seeding

# COMMAND ----------

# Initialize Spark
spark = SparkSession.builder.appName("seed_config").getOrCreate()

# Configuration
CATALOG = "main"
SCHEMA = "config"
TABLE = f"{CATALOG}.{SCHEMA}.search_terms"

print("=" * 70)
print("CONFIGURATION DATA SEEDING")
print("=" * 70)
print(f"Target Table: {TABLE}")
print("=" * 70)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Schema

# COMMAND ----------

print("\n[STEP 1] Creating config schema...")

try:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
    print(f"✅ Schema created/verified: {CATALOG}.{SCHEMA}")
except Exception as e:
    print(f"❌ Error creating schema: {e}")
    dbutils.notebook.exit(f"Failed to create schema: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create Search Terms Table

# COMMAND ----------

print("\n[STEP 2] Creating search_terms table...")

# Define schema for search terms table
search_terms_schema = StructType([
    StructField("term", StringType(), False),           # Search term (primary key)
    StructField("active", BooleanType(), True),          # Whether term is active
    StructField("category", StringType(), True),         # Category (e.g., "AI", "Database", "Tool")
    StructField("description", StringType(), True),      # Description of what this term tracks
    StructField("created_at", TimestampType(), True),    # When term was added
    StructField("updated_at", TimestampType(), True)     # Last update timestamp
])

try:
    # Check if table exists
    if not spark.catalog.tableExists(TABLE):
        # Create empty table with schema
        empty_df = spark.createDataFrame([], search_terms_schema)
        empty_df.write.format("delta") \
            .mode("overwrite") \
            .saveAsTable(TABLE)
        print(f"✅ Table created: {TABLE}")
    else:
        print(f"✅ Table already exists: {TABLE}")

    # Show current schema
    print("\nTable schema:")
    spark.read.format("delta").table(TABLE).printSchema()

except Exception as e:
    print(f"❌ Error creating table: {e}")
    dbutils.notebook.exit(f"Failed to create table: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Define Seed Data

# COMMAND ----------

print("\n[STEP 3] Defining seed data...")

# Default search terms for AI newsletter
seed_terms = [
    {
        "term": "Gemini",
        "active": True,
        "category": "AI",
        "description": "Google's Gemini AI model and products"
    },
    {
        "term": "Databricks",
        "active": True,
        "category": "Database",
        "description": "Databricks data lakehouse platform"
    },
    {
        "term": "Claude Code",
        "active": True,
        "category": "Tool",
        "description": "Anthropic's Claude Code development tool"
    },
    {
        "term": "Claude",
        "active": True,
        "category": "AI",
        "description": "Anthropic's Claude AI assistant"
    },
    {
        "term": "AI Driven Development",
        "active": True,
        "category": "Trend",
        "description": "AI-assisted software development trend"
    },
    {
        "term": "GPT-4",
        "active": True,
        "category": "AI",
        "description": "OpenAI's GPT-4 language model"
    },
    {
        "term": "ChatGPT",
        "active": True,
        "category": "Tool",
        "description": "OpenAI's ChatGPT conversational AI"
    },
    {
        "term": "LLM",
        "active": True,
        "category": "AI",
        "description": "Large Language Models in general"
    },
    {
        "term": "Machine Learning",
        "active": True,
        "category": "AI",
        "description": "General machine learning discussions"
    },
    {
        "term": "Delta Lake",
        "active": True,
        "category": "Database",
        "description": "Delta Lake open-source storage layer"
    }
]

print(f"Defined {len(seed_terms)} search terms to seed")
print("\nSearch terms:")
for term in seed_terms:
    status = "🟢" if term["active"] else "🔴"
    print(f"  {status} {term['term']} ({term['category']})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Seed Data (Upsert)

# COMMAND ----------

print("\n[STEP 4] Seeding search terms...")

try:
    # Read existing data
    existing_df = spark.read.format("delta").table(TABLE)
    existing_count = existing_df.count()
    print(f"Current records in table: {existing_count}")

    # Create DataFrame from seed data with explicit schema
    from pyspark.sql import Row
    from datetime import datetime

    seed_rows = []
    current_time = datetime.now()

    for term_data in seed_terms:
        seed_rows.append(Row(
            term=term_data["term"],
            active=term_data["active"],
            category=term_data["category"],
            description=term_data["description"],
            created_at=current_time,
            updated_at=current_time
        ))

    seed_df = spark.createDataFrame(seed_rows, schema=search_terms_schema)

    # Perform upsert using merge
    # If term exists, update it; otherwise insert it
    from delta.tables import DeltaTable

    delta_table = DeltaTable.forName(spark, TABLE)

    delta_table.alias("existing") \
        .merge(
            seed_df.alias("updates"),
            "existing.term = updates.term"
        ) \
        .whenMatchedUpdate(set={
            "active": "updates.active",
            "category": "updates.category",
            "description": "updates.description",
            "updated_at": "updates.updated_at"
        }) \
        .whenNotMatchedInsertAll() \
        .execute()

    # Count records after seeding
    final_df = spark.read.format("delta").table(TABLE)
    final_count = final_df.count()

    new_records = final_count - existing_count
    updated_records = len(seed_terms) - new_records

    print(f"\n✅ Seeding complete!")
    print(f"   Total records: {final_count}")
    print(f"   New records: {new_records}")
    print(f"   Updated records: {updated_records}")

except Exception as e:
    print(f"❌ Error seeding data: {e}")
    import traceback
    traceback.print_exc()
    dbutils.notebook.exit(f"Failed to seed data: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Seeded Data

# COMMAND ----------

print("\n[STEP 5] Verifying seeded data...")

try:
    # Read and display seeded data
    result_df = spark.read.format("delta").table(TABLE)

    print(f"\nAll search terms in {TABLE}:")
    result_df.orderBy("category", "term").show(truncate=False)

    # Show statistics
    print("\nStatistics by category:")
    result_df.groupBy("category").count().orderBy("category").show()

    print("\nActive vs Inactive terms:")
    result_df.groupBy("active").count().show()

except Exception as e:
    print(f"❌ Error verifying data: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Test Query String Generation

# COMMAND ----------

print("\n[STEP 6] Testing query string generation...")

try:
    # Generate the query string as it will be used in Twitter ingestion
    active_terms_df = spark.read.format("delta").table(TABLE).filter("active = true")
    active_terms = [row.term for row in active_terms_df.collect()]

    query_string = " OR ".join(active_terms) + " lang:en -is:retweet"

    print(f"\nActive search terms: {len(active_terms)}")
    print(f"\nGenerated Twitter query string:")
    print(f"  {query_string}")
    print(f"\nQuery string length: {len(query_string)} characters")

    # Twitter API has a 512 character limit for query strings
    if len(query_string) > 512:
        print(f"\n⚠️  WARNING: Query string exceeds Twitter API limit of 512 characters!")
        print(f"   Consider reducing number of search terms or using shorter terms")
    else:
        print(f"\n✅ Query string is within Twitter API limit (512 characters)")

except Exception as e:
    print(f"❌ Error testing query: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 70)
print("SEEDING COMPLETE")
print("=" * 70)

try:
    final_stats = spark.read.format("delta").table(TABLE)
    total = final_stats.count()
    active = final_stats.filter("active = true").count()
    inactive = total - active

    print(f"\n✅ Configuration table seeded: {TABLE}")
    print(f"   Total search terms: {total}")
    print(f"   Active terms: {active}")
    print(f"   Inactive terms: {inactive}")

    print(f"\nTo add more terms:")
    print(f"  1. Add to seed_terms list in this script")
    print(f"  2. Run this notebook again (safe to rerun)")
    print(f"  3. Or insert directly:")
    print(f"     INSERT INTO {TABLE} VALUES ('term', true, 'category', 'description', current_timestamp(), current_timestamp())")

    print(f"\nTo deactivate a term:")
    print(f"  UPDATE {TABLE} SET active = false WHERE term = 'term_name'")

    print(f"\nView all terms:")
    print(f"  SELECT * FROM {TABLE} ORDER BY category, term")

except Exception as e:
    print(f"❌ Error generating summary: {e}")

print("=" * 70)
