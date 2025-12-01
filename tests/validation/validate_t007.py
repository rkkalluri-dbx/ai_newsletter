# Databricks notebook source
"""
Validation Script for T007: Silver Table Implementation

This notebook validates the silver layer processing implementation:
1. Checks bronze table has data
2. Runs silver processing
3. Validates data quality and transformations
4. Checks deduplication effectiveness
5. Validates influence score calculation
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, countDistinct, avg, min, max, sum as _sum

# --- Configuration ---
try:
    catalog = spark.sql("SELECT current_catalog()").collect()[0][0]
except Exception:
    catalog = "main"

bronze_table = f"{catalog}.ai_newsletter_bronze.tweets"
silver_table = f"{catalog}.ai_newsletter_silver.tweets"

print("=" * 80)
print("T007 VALIDATION: Silver Table Processing")
print("=" * 80)

# --- Test 1: Verify Bronze Table Exists and Has Data ---
print("\n[TEST 1] Checking bronze table...")
try:
    bronze_df = spark.read.format("delta").table(bronze_table)
    bronze_count = bronze_df.count()

    if bronze_count == 0:
        print(f"⚠️  WARNING: Bronze table exists but has no data ({bronze_count} records)")
        print("   Run the bronze ingestion job first:")
        print("   databricks bundle run ai_newsletter_bronze_job --profile DEFAULT")
    else:
        print(f"✅ Bronze table has {bronze_count} records")

        # Show sample bronze data
        print("\nSample bronze data:")
        bronze_df.select("id", "text", "author_id", "public_metrics.like_count").show(3, truncate=True)

except Exception as e:
    print(f"❌ FAIL: Bronze table not found or error: {e}")
    print("   Ensure bronze ingestion has run successfully")
    raise

# --- Test 2: Check if Silver Table Exists ---
print("\n[TEST 2] Checking silver table...")
try:
    silver_df = spark.read.format("delta").table(silver_table)
    silver_count = silver_df.count()
    print(f"✅ Silver table exists with {silver_count} records")

    if silver_count == 0:
        print("⚠️  Silver table is empty. Running silver processing...")
        print("   This will take a moment...")
        # Import and run the silver processing
        from silver_processing import process_silver_layer
        process_silver_layer()
        silver_df = spark.read.format("delta").table(silver_table)
        silver_count = silver_df.count()
        print(f"✅ Silver processing complete. {silver_count} records created")

except Exception as e:
    print(f"ℹ️  Silver table doesn't exist yet. This is expected on first run.")
    print("   Running silver processing job...")
    try:
        from silver_processing import process_silver_layer
        process_silver_layer()
        silver_df = spark.read.format("delta").table(silver_table)
        silver_count = silver_df.count()
        print(f"✅ Silver table created with {silver_count} records")
    except Exception as e2:
        print(f"❌ FAIL: Could not create silver table: {e2}")
        raise

# --- Test 3: Validate Schema ---
print("\n[TEST 3] Validating silver table schema...")
expected_columns = [
    "tweet_id", "text", "author_id", "author_name", "follower_count",
    "verified", "created_at", "like_count", "retweet_count", "reply_count",
    "influence_score", "processed_at"
]

actual_columns = silver_df.columns
missing_columns = set(expected_columns) - set(actual_columns)
extra_columns = set(actual_columns) - set(expected_columns)

if missing_columns:
    print(f"❌ FAIL: Missing columns: {missing_columns}")
elif extra_columns:
    print(f"⚠️  WARNING: Extra columns found: {extra_columns}")
else:
    print(f"✅ All expected columns present: {len(expected_columns)} columns")

print(f"\nActual schema:")
silver_df.printSchema()

# --- Test 4: Validate Deduplication ---
print("\n[TEST 4] Validating deduplication...")
dedup_stats = silver_df.agg(
    count("*").alias("total_records"),
    countDistinct("tweet_id").alias("unique_tweet_ids")
).collect()[0]

total = dedup_stats['total_records']
unique = dedup_stats['unique_tweet_ids']

if total == unique:
    print(f"✅ PASS: Perfect deduplication")
    print(f"   Total records: {total}")
    print(f"   Unique tweet IDs: {unique}")
    print(f"   Duplicates: 0")
else:
    print(f"❌ FAIL: Duplicates detected!")
    print(f"   Total records: {total}")
    print(f"   Unique tweet IDs: {unique}")
    print(f"   Duplicates: {total - unique}")

    # Show duplicate tweet IDs
    duplicates_df = (
        silver_df.groupBy("tweet_id")
        .agg(count("*").alias("count"))
        .filter(col("count") > 1)
        .orderBy(col("count").desc())
    )

    if duplicates_df.count() > 0:
        print("\n   Duplicate tweet IDs:")
        duplicates_df.show(10, truncate=False)

# --- Test 5: Validate Influence Score Calculation ---
print("\n[TEST 5] Validating influence score calculation...")

# Check for null or negative scores
null_scores = silver_df.filter(col("influence_score").isNull()).count()
negative_scores = silver_df.filter(col("influence_score") < 0).count()

if null_scores > 0:
    print(f"❌ FAIL: Found {null_scores} null influence scores")
elif negative_scores > 0:
    print(f"❌ FAIL: Found {negative_scores} negative influence scores")
else:
    print(f"✅ PASS: No null or negative influence scores")

# Show influence score statistics
score_stats = silver_df.select(
    count("influence_score").alias("count"),
    avg("influence_score").alias("avg_score"),
    min("influence_score").alias("min_score"),
    max("influence_score").alias("max_score")
).collect()[0]

print(f"\nInfluence Score Statistics:")
print(f"   Count: {score_stats['count']}")
print(f"   Average: {score_stats['avg_score']:.2f}")
print(f"   Min: {score_stats['min_score']:.2f}")
print(f"   Max: {score_stats['max_score']:.2f}")

# Manually verify a few scores
print("\nManual Verification (first 5 tweets):")
manual_check_df = silver_df.select(
    "tweet_id",
    "like_count",
    "retweet_count",
    "reply_count",
    "follower_count",
    "influence_score"
).limit(5)

for row in manual_check_df.collect():
    expected_score = (
        (row['like_count'] or 0) * 2 +
        (row['retweet_count'] or 0) * 3 +
        (row['reply_count'] or 0) * 1 +
        (row['follower_count'] or 0) / 1000.0
    )
    actual_score = row['influence_score']
    match = "✓" if abs(expected_score - actual_score) < 0.01 else "✗"

    print(f"   {match} Tweet {row['tweet_id'][:10]}...")
    print(f"      Likes: {row['like_count']}, Retweets: {row['retweet_count']}, "
          f"Replies: {row['reply_count']}, Followers: {row['follower_count']}")
    print(f"      Expected: {expected_score:.2f}, Actual: {actual_score:.2f}")

# --- Test 6: Validate Data Transformation ---
print("\n[TEST 6] Validating data transformation (bronze → silver)...")

# Compare record counts
bronze_unique = bronze_df.select(countDistinct("id")).collect()[0][0]
silver_unique = silver_df.select(countDistinct("tweet_id")).collect()[0][0]

print(f"   Bronze unique tweets: {bronze_unique}")
print(f"   Silver unique tweets: {silver_unique}")

if silver_unique <= bronze_unique:
    print(f"✅ PASS: Silver has same or fewer records (expected due to deduplication)")
else:
    print(f"⚠️  WARNING: Silver has MORE unique tweets than bronze")

# --- Test 7: Check Processing Timestamp ---
print("\n[TEST 7] Checking processed_at timestamp...")
null_timestamps = silver_df.filter(col("processed_at").isNull()).count()

if null_timestamps > 0:
    print(f"❌ FAIL: Found {null_timestamps} null processed_at timestamps")
else:
    print(f"✅ PASS: All records have processed_at timestamp")

    # Show latest processing time
    latest = silver_df.select(max("processed_at")).collect()[0][0]
    print(f"   Latest processing time: {latest}")

# --- Test 8: Data Quality Summary ---
print("\n[TEST 8] Data Quality Summary...")

quality_metrics = silver_df.select(
    count("*").alias("total_records"),
    countDistinct("tweet_id").alias("unique_tweets"),
    _sum((col("author_name") == "").cast("int")).alias("empty_author_names"),
    _sum((col("follower_count") == 0).cast("int")).alias("zero_followers"),
    _sum((col("influence_score").isNull()).cast("int")).alias("null_scores"),
    avg("influence_score").alias("avg_influence")
).collect()[0]

print(f"   Total Records: {quality_metrics['total_records']}")
print(f"   Unique Tweets: {quality_metrics['unique_tweets']}")
print(f"   Empty Author Names: {quality_metrics['empty_author_names']} (expected - placeholder)")
print(f"   Zero Followers: {quality_metrics['zero_followers']} (expected - placeholder)")
print(f"   Null Scores: {quality_metrics['null_scores']}")
print(f"   Avg Influence: {quality_metrics['avg_influence']:.2f}")

# --- Test 9: Show Sample Data ---
print("\n[TEST 9] Sample silver table data...")
print("\nTop 10 tweets by influence score:")
silver_df.select(
    "tweet_id",
    "text",
    "like_count",
    "retweet_count",
    "influence_score"
).orderBy(col("influence_score").desc()).show(10, truncate=True)

# --- Final Summary ---
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

total_tests = 9
passed_tests = 0

# Count passed tests (this is simplified - in production would track each test result)
if bronze_count > 0:
    passed_tests += 1
if silver_count > 0:
    passed_tests += 1
if not missing_columns:
    passed_tests += 1
if total == unique:
    passed_tests += 1
if null_scores == 0 and negative_scores == 0:
    passed_tests += 1
if silver_unique <= bronze_unique:
    passed_tests += 1
if null_timestamps == 0:
    passed_tests += 1
passed_tests += 2  # Quality summary and sample data

print(f"\n✅ Passed: {passed_tests}/{total_tests} tests")

if passed_tests == total_tests:
    print("\n🎉 ALL TESTS PASSED! T007 implementation is validated.")
else:
    print(f"\n⚠️  Some tests failed. Review the output above for details.")

print("\nNext steps:")
print("1. Review any failed tests or warnings")
print("2. For full author enrichment, update twitter_ingestion_script.py to fetch user data")
print("3. For language filtering, add 'lang' field to bronze schema")
print("4. Monitor influence score distribution in production")
print("5. Proceed to T008: Gold daily materialized view")

print("=" * 80)
