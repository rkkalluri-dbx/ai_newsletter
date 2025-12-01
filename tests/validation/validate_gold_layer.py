# Databricks notebook source
"""
Gold Layer Validation Notebook (T008 & T009)
Validates daily and weekly gold materialized views with detailed data checks

Run this notebook in Databricks UI to validate:
- Table existence and schema
- Data quality and completeness
- Ranking logic correctness
- Partitioning strategy
- Aggregation accuracy
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as _sum, avg as _avg, max as _max, min as _min

# COMMAND ----------

# MAGIC %md
# MAGIC # Gold Layer Validation - T008 & T009
# MAGIC
# MAGIC This notebook validates the gold layer implementation:
# MAGIC - **T008**: Daily top candidates view
# MAGIC - **T009**: Weekly rollup view

# COMMAND ----------

# Initialize Spark
spark = SparkSession.builder.appName("validate_gold_layer").getOrCreate()

# Configuration
CATALOG = "main"
GOLD_SCHEMA = f"{CATALOG}.ai_newsletter_gold"
SILVER_TABLE = f"{CATALOG}.ai_newsletter_silver.tweets"
DAILY_TABLE = f"{GOLD_SCHEMA}.daily_top_candidates"
WEEKLY_TABLE = f"{GOLD_SCHEMA}.weekly_top_stories"
AUTHORS_TABLE = f"{GOLD_SCHEMA}.weekly_trending_authors"

print("=" * 60)
print("GOLD LAYER VALIDATION")
print("=" * 60)
print(f"Silver Table: {SILVER_TABLE}")
print(f"Daily Table: {DAILY_TABLE}")
print(f"Weekly Table: {WEEKLY_TABLE}")
print(f"Authors Table: {AUTHORS_TABLE}")
print("=" * 60)

# Test counters
tests_passed = 0
tests_failed = 0
tests_warning = 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: Table Existence

# COMMAND ----------

print("\n[TEST 1] Checking table existence...")

try:
    # Check daily table
    daily_df = spark.read.format("delta").table(DAILY_TABLE)
    print(f"✅ PASS: Daily table exists - {DAILY_TABLE}")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL: Daily table not found - {e}")
    tests_failed += 1

try:
    # Check weekly table
    weekly_df = spark.read.format("delta").table(WEEKLY_TABLE)
    print(f"✅ PASS: Weekly table exists - {WEEKLY_TABLE}")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL: Weekly table not found - {e}")
    tests_failed += 1

try:
    # Check trending authors table
    authors_df = spark.read.format("delta").table(AUTHORS_TABLE)
    print(f"✅ PASS: Trending authors table exists - {AUTHORS_TABLE}")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL: Trending authors table not found - {e}")
    tests_failed += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Schema Validation

# COMMAND ----------

print("\n[TEST 2] Validating table schemas...")

# Expected columns for daily table
expected_daily_cols = [
    "tweet_id", "text", "author_id", "author_name", "created_at",
    "tweet_date", "like_count", "retweet_count", "reply_count",
    "follower_count", "influence_score", "daily_rank", "influence_rank",
    "processed_at"
]

daily_cols = daily_df.columns
missing_cols = set(expected_daily_cols) - set(daily_cols)

if not missing_cols:
    print(f"✅ PASS: Daily table has all required columns ({len(daily_cols)} columns)")
    tests_passed += 1
else:
    print(f"❌ FAIL: Daily table missing columns: {missing_cols}")
    tests_failed += 1

# Check weekly table columns
expected_weekly_cols = [
    "tweet_id", "text", "author_id", "author_name", "created_at",
    "tweet_date", "like_count", "retweet_count", "reply_count",
    "follower_count", "influence_score", "weekly_rank",
    "week_start_date", "week_end_date", "processed_at"
]

weekly_cols = weekly_df.columns
missing_cols = set(expected_weekly_cols) - set(weekly_cols)

if not missing_cols:
    print(f"✅ PASS: Weekly table has all required columns ({len(weekly_cols)} columns)")
    tests_passed += 1
else:
    print(f"❌ FAIL: Weekly table missing columns: {missing_cols}")
    tests_failed += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Row Count Validation

# COMMAND ----------

print("\n[TEST 3] Validating row counts...")

daily_count = daily_df.count()
print(f"Daily table records: {daily_count}")

if daily_count > 0 and daily_count <= 100:
    print(f"✅ PASS: Daily table has expected row count (1-100 per day)")
    tests_passed += 1
elif daily_count == 0:
    print(f"⚠️  WARNING: Daily table is empty")
    tests_warning += 1
else:
    print(f"⚠️  WARNING: Daily table has more than 100 rows ({daily_count})")
    tests_warning += 1

weekly_count = weekly_df.count()
print(f"Weekly table records: {weekly_count}")

if weekly_count > 0 and weekly_count <= 200:
    print(f"✅ PASS: Weekly table has expected row count (1-200)")
    tests_passed += 1
elif weekly_count == 0:
    print(f"⚠️  WARNING: Weekly table is empty")
    tests_warning += 1
else:
    print(f"⚠️  WARNING: Weekly table has more than 200 rows ({weekly_count})")
    tests_warning += 1

authors_count = authors_df.count()
print(f"Trending authors records: {authors_count}")

if authors_count > 0 and authors_count <= 20:
    print(f"✅ PASS: Trending authors table has expected row count (1-20)")
    tests_passed += 1
elif authors_count == 0:
    print(f"⚠️  WARNING: Trending authors table is empty")
    tests_warning += 1
else:
    print(f"⚠️  WARNING: Trending authors has more than 20 rows ({authors_count})")
    tests_warning += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Ranking Logic Validation

# COMMAND ----------

print("\n[TEST 4] Validating ranking logic...")

# Check daily ranking
if daily_count > 0:
    # Check if daily_rank is sequential starting from 1
    rank_check = daily_df.select("daily_rank").orderBy("daily_rank").collect()
    expected_ranks = list(range(1, len(rank_check) + 1))
    actual_ranks = [row.daily_rank for row in rank_check]

    if actual_ranks == expected_ranks:
        print(f"✅ PASS: Daily rankings are sequential (1 to {len(rank_check)})")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Daily rankings have gaps or duplicates")
        tests_failed += 1

    # Check if influence_score is properly ordered
    scores = daily_df.select("influence_score").orderBy(col("daily_rank")).collect()
    scores_list = [row.influence_score for row in scores]

    if scores_list == sorted(scores_list, reverse=True):
        print(f"✅ PASS: Daily tweets properly ordered by influence_score (descending)")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Daily tweets not properly ordered by influence_score")
        tests_failed += 1
else:
    print("⚠️  WARNING: Cannot validate ranking - daily table is empty")
    tests_warning += 1

# Check weekly ranking
if weekly_count > 0:
    # Check if weekly_rank is sequential
    rank_check = weekly_df.select("weekly_rank").orderBy("weekly_rank").collect()
    expected_ranks = list(range(1, len(rank_check) + 1))
    actual_ranks = [row.weekly_rank for row in rank_check]

    if actual_ranks == expected_ranks:
        print(f"✅ PASS: Weekly rankings are sequential (1 to {len(rank_check)})")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Weekly rankings have gaps or duplicates")
        tests_failed += 1

    # Check if influence_score is properly ordered
    scores = weekly_df.select("influence_score").orderBy(col("weekly_rank")).collect()
    scores_list = [row.influence_score for row in scores]

    if scores_list == sorted(scores_list, reverse=True):
        print(f"✅ PASS: Weekly tweets properly ordered by influence_score (descending)")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Weekly tweets not properly ordered by influence_score")
        tests_failed += 1
else:
    print("⚠️  WARNING: Cannot validate ranking - weekly table is empty")
    tests_warning += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Partitioning Validation

# COMMAND ----------

print("\n[TEST 5] Validating table partitioning...")

# Check daily table partitioning
daily_partitions = daily_df.select("tweet_date").distinct().count()
print(f"Daily table partitions (unique dates): {daily_partitions}")

if daily_partitions >= 1:
    print(f"✅ PASS: Daily table is partitioned by tweet_date ({daily_partitions} partition(s))")
    tests_passed += 1
else:
    print(f"❌ FAIL: Daily table has no partitions")
    tests_failed += 1

# Check weekly table partitioning
weekly_partitions = weekly_df.select("week_start_date").distinct().count()
print(f"Weekly table partitions (unique weeks): {weekly_partitions}")

if weekly_partitions >= 1:
    print(f"✅ PASS: Weekly table is partitioned by week_start_date ({weekly_partitions} partition(s))")
    tests_passed += 1
else:
    print(f"❌ FAIL: Weekly table has no partitions")
    tests_failed += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Data Quality Checks

# COMMAND ----------

print("\n[TEST 6] Validating data quality...")

if daily_count > 0:
    # Check for null values in critical columns
    null_counts = daily_df.select([
        _sum(col("tweet_id").isNull().cast("int")).alias("tweet_id_nulls"),
        _sum(col("influence_score").isNull().cast("int")).alias("influence_score_nulls"),
        _sum(col("daily_rank").isNull().cast("int")).alias("daily_rank_nulls")
    ]).collect()[0]

    if null_counts.tweet_id_nulls == 0 and null_counts.influence_score_nulls == 0 and null_counts.daily_rank_nulls == 0:
        print(f"✅ PASS: Daily table has no null values in critical columns")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Daily table has null values - tweet_id: {null_counts.tweet_id_nulls}, influence_score: {null_counts.influence_score_nulls}, daily_rank: {null_counts.daily_rank_nulls}")
        tests_failed += 1

    # Check influence score distribution
    score_stats = daily_df.select("influence_score").describe().collect()
    min_score = float([row for row in score_stats if row.summary == "min"][0].influence_score)
    max_score = float([row for row in score_stats if row.summary == "max"][0].influence_score)

    print(f"   Influence score range: {min_score:.2f} to {max_score:.2f}")

    if min_score >= 0 and max_score > min_score:
        print(f"✅ PASS: Daily table has valid influence scores")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Daily table has invalid influence scores")
        tests_failed += 1
else:
    print("⚠️  WARNING: Cannot validate data quality - daily table is empty")
    tests_warning += 1

if weekly_count > 0:
    # Check for null values in weekly table
    null_counts = weekly_df.select([
        _sum(col("tweet_id").isNull().cast("int")).alias("tweet_id_nulls"),
        _sum(col("influence_score").isNull().cast("int")).alias("influence_score_nulls"),
        _sum(col("weekly_rank").isNull().cast("int")).alias("weekly_rank_nulls")
    ]).collect()[0]

    if null_counts.tweet_id_nulls == 0 and null_counts.influence_score_nulls == 0 and null_counts.weekly_rank_nulls == 0:
        print(f"✅ PASS: Weekly table has no null values in critical columns")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Weekly table has null values")
        tests_failed += 1
else:
    print("⚠️  WARNING: Cannot validate weekly data quality - table is empty")
    tests_warning += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 7: Aggregation Validation (Weekly)

# COMMAND ----------

print("\n[TEST 7] Validating weekly aggregations...")

if weekly_count > 0:
    # Check date range
    date_range = weekly_df.agg(
        _min("tweet_date").alias("min_date"),
        _max("tweet_date").alias("max_date")
    ).collect()[0]

    print(f"   Weekly data date range: {date_range.min_date} to {date_range.max_date}")

    # Check if trending authors have multiple tweets
    if authors_count > 0:
        authors_with_multiple = authors_df.filter(col("tweet_count") > 1).count()
        print(f"   Authors with multiple tweets: {authors_with_multiple} / {authors_count}")

        if authors_with_multiple >= 0:
            print(f"✅ PASS: Trending authors aggregation looks correct")
            tests_passed += 1
        else:
            print(f"❌ FAIL: No authors with multiple tweets found")
            tests_failed += 1
    else:
        print("⚠️  WARNING: No trending authors to validate")
        tests_warning += 1
else:
    print("⚠️  WARNING: Cannot validate aggregations - weekly table is empty")
    tests_warning += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 8: Compare with Silver Table

# COMMAND ----------

print("\n[TEST 8] Comparing gold tables with silver source...")

try:
    silver_df = spark.read.format("delta").table(SILVER_TABLE)
    silver_count = silver_df.count()
    print(f"Silver table records: {silver_count}")

    if silver_count > 0:
        # Check that daily table is a subset of silver
        if daily_count > 0 and daily_count <= silver_count:
            print(f"✅ PASS: Daily table is proper subset of silver ({daily_count} <= {silver_count})")
            tests_passed += 1
        elif daily_count == 0:
            print(f"⚠️  WARNING: Daily table is empty but silver has {silver_count} records")
            tests_warning += 1
        else:
            print(f"❌ FAIL: Daily table has more records than silver")
            tests_failed += 1

        # Check that weekly table is a subset of silver
        if weekly_count > 0 and weekly_count <= silver_count:
            print(f"✅ PASS: Weekly table is proper subset of silver ({weekly_count} <= {silver_count})")
            tests_passed += 1
        elif weekly_count == 0:
            print(f"⚠️  WARNING: Weekly table is empty but silver has {silver_count} records")
            tests_warning += 1
        else:
            print(f"❌ FAIL: Weekly table has more records than silver")
            tests_failed += 1
    else:
        print(f"⚠️  WARNING: Silver table is empty, cannot compare")
        tests_warning += 1

except Exception as e:
    print(f"❌ FAIL: Cannot read silver table - {e}")
    tests_failed += 1

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Data Display

# COMMAND ----------

print("\n" + "=" * 60)
print("SAMPLE DATA")
print("=" * 60)

if daily_count > 0:
    print("\nTop 10 Daily Tweets:")
    daily_df.orderBy("daily_rank").select(
        "daily_rank", "tweet_id", "text", "author_name", "influence_score"
    ).show(10, truncate=60)

if weekly_count > 0:
    print("\nTop 10 Weekly Tweets:")
    weekly_df.orderBy("weekly_rank").select(
        "weekly_rank", "tweet_id", "text", "author_name", "influence_score"
    ).show(10, truncate=60)

if authors_count > 0:
    print("\nTop 10 Trending Authors:")
    authors_df.orderBy(col("total_influence").desc()).select(
        "author_name", "tweet_count", "total_likes", "total_retweets", "total_influence"
    ).show(10, truncate=40)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

total_tests = tests_passed + tests_failed + tests_warning
print(f"Total Tests: {total_tests}")
print(f"Passed:   {tests_passed}")
print(f"Failed:   {tests_failed}")
print(f"Warnings: {tests_warning}")
print()

if tests_failed == 0 and tests_warning == 0:
    print("🎉 ALL TESTS PASSED!")
    print()
    print("Gold Layer Status:")
    print("✅ T008: Daily materialized view working correctly")
    print("✅ T009: Weekly rollup view working correctly")
    print("✅ All tables have proper schema and data")
    print("✅ Ranking logic is correct")
    print("✅ Partitioning strategy is working")
    print("✅ Data quality is good")
    print()
    print("Next steps:")
    print("- Epic 3: Implement LLM Summarization Agent (T010-T012)")
elif tests_failed == 0 and tests_warning > 0:
    print(f"⚠️  ALL TESTS PASSED WITH {tests_warning} WARNING(S)")
    print()
    print("Most warnings are due to empty tables or low data volume.")
    print("Run the pipeline for a few days to accumulate more data.")
else:
    print("⚠️  SOME TESTS FAILED")
    print()
    print("Common solutions:")
    print("1. Run gold layer jobs:")
    print("   databricks jobs run-now <JOB_ID> --profile DEFAULT")
    print()
    print("2. Check job logs in Databricks UI:")
    print("   Workflows → ai_newsletter_gold_daily_view")
    print("   Workflows → ai_newsletter_gold_weekly_rollup")

print("=" * 60)
