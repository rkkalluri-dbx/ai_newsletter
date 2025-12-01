# Databricks notebook source
# MAGIC %md
# MAGIC # Twitter Ingestion Validation
# MAGIC
# MAGIC This notebook validates that Twitter ingestion is working correctly with real Twitter API data.
# MAGIC
# MAGIC **Tests Performed:**
# MAGIC 1. Secret configuration validation
# MAGIC 2. Raw tweet files verification
# MAGIC 3. Tweet ID format validation (real vs dummy)
# MAGIC 4. API response structure validation
# MAGIC 5. Data freshness check
# MAGIC 6. Search terms configuration
# MAGIC 7. Bronze table ingestion
# MAGIC 8. Volume accessibility

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: Secret Configuration

# COMMAND ----------

import json
from datetime import datetime, timedelta

# Test secret retrieval
print("=" * 60)
print("TEST 1: SECRET CONFIGURATION")
print("=" * 60)

try:
    bearer_token = dbutils.secrets.get(scope="ai_newsletter_config", key="twitter_bearer_token")

    # Check if it's the placeholder
    if bearer_token == "YOUR_TWITTER_BEARER_TOKEN_HERE":
        print("❌ FAIL: Secret exists but contains placeholder value")
        print("   Action: Update secret with real Twitter bearer token")
        secret_configured = False
    elif len(bearer_token) < 20:
        print("⚠️  WARNING: Secret value seems too short to be a valid bearer token")
        print(f"   Token length: {len(bearer_token)} characters")
        print("   Expected: 100+ characters for valid Twitter bearer token")
        secret_configured = False
    else:
        print("✅ PASS: Secret configured correctly")
        print(f"   Token length: {len(bearer_token)} characters")
        print(f"   Token prefix: {bearer_token[:10]}...")
        secret_configured = True

except Exception as e:
    print(f"❌ FAIL: Could not retrieve secret from ai_newsletter_config scope")
    print(f"   Error: {e}")
    print("   Action: Create secret with:")
    print("   databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT")
    secret_configured = False

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Search Terms Configuration

# COMMAND ----------

print("=" * 60)
print("TEST 2: SEARCH TERMS CONFIGURATION")
print("=" * 60)

catalog_name = spark.sql("SELECT current_catalog()").collect()[0][0]
schema_name = "config"
search_terms_table = f"{catalog_name}.{schema_name}.search_terms"

# Create schema if needed
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

# Check if table exists
if spark.catalog.tableExists(search_terms_table):
    search_terms_df = spark.sql(f"SELECT * FROM {search_terms_table}")
    search_terms_count = search_terms_df.count()

    if search_terms_count == 0:
        print("⚠️  WARNING: Search terms table exists but is empty")
        print("   Using default terms: Gemini, Databricks, Claude Code, Claude, AI Driven Development")
    else:
        print(f"✅ PASS: Search terms table configured with {search_terms_count} terms")
        print("\n   Configured terms:")
        for row in search_terms_df.collect():
            print(f"   - {row.term}")
else:
    print("⚠️  WARNING: Search terms table does not exist")
    print(f"   Table: {search_terms_table}")
    print("   Using default terms: Gemini, Databricks, Claude Code, Claude, AI Driven Development")
    print("\n   To create table:")
    print(f"   CREATE TABLE {search_terms_table} (term STRING);")
    print(f"   INSERT INTO {search_terms_table} VALUES ('claude code'), ('databricks'), ('gemini');")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Raw Tweet Files Analysis

# COMMAND ----------

print("=" * 60)
print("TEST 3: RAW TWEET FILES ANALYSIS")
print("=" * 60)

raw_data_path = "/Volumes/main/default/ai_newsletter_raw_tweets/"

try:
    # List files
    files = dbutils.fs.ls(raw_data_path)

    # Filter only tweet JSON files (exclude _checkpoint and _schema)
    tweet_files = [f for f in files if f.name.startswith("tweet_") and f.name.endswith(".json")]

    if len(tweet_files) == 0:
        print("❌ FAIL: No tweet files found in UC Volume")
        print(f"   Path: {raw_data_path}")
    else:
        print(f"✅ Total tweet files found: {len(tweet_files)}")

        # Count dummy vs real tweets
        dummy_count = sum(1 for f in tweet_files if "dummy" in f.name)
        real_count = len(tweet_files) - dummy_count

        print(f"\n   📊 File Breakdown:")
        print(f"   - Dummy tweets: {dummy_count}")
        print(f"   - Real tweets:  {real_count}")

        if real_count == 0:
            print("\n   ❌ FAIL: All tweets are dummy data - Twitter API not being called")
            print("   Reason: Bearer token not configured or invalid")
        else:
            print(f"\n   ✅ PASS: Found {real_count} real tweets from Twitter API")

        # Check most recent files
        print(f"\n   📅 Most Recent Files (last 5):")
        recent_files = sorted(tweet_files, key=lambda f: f.modificationTime, reverse=True)[:5]
        for f in recent_files:
            timestamp = datetime.fromtimestamp(f.modificationTime / 1000)
            age = datetime.now() - timestamp
            file_type = "DUMMY" if "dummy" in f.name else "REAL"
            print(f"   [{file_type}] {f.name} - {age.seconds // 60} min ago")

        # Sample a recent file
        if len(recent_files) > 0:
            sample_file = recent_files[0]
            print(f"\n   📄 Sample Tweet Content ({sample_file.name}):")
            try:
                content = dbutils.fs.head(sample_file.path, 1000)
                tweet_data = json.loads(content)
                print(f"   - Tweet ID: {tweet_data.get('id', 'N/A')}")
                print(f"   - Text: {tweet_data.get('text', 'N/A')[:80]}...")
                print(f"   - Author ID: {tweet_data.get('author_id', 'N/A')}")

                # Check if it has real Twitter structure
                if 'public_metrics' in tweet_data:
                    metrics = tweet_data['public_metrics']
                    print(f"   - Likes: {metrics.get('like_count', 0)}")
                    print(f"   - Retweets: {metrics.get('retweet_count', 0)}")
                    print(f"   - Replies: {metrics.get('reply_count', 0)}")

            except Exception as e:
                print(f"   ⚠️  Could not parse file: {e}")

except Exception as e:
    print(f"❌ FAIL: Could not access UC Volume")
    print(f"   Path: {raw_data_path}")
    print(f"   Error: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Bronze Table Validation

# COMMAND ----------

print("=" * 60)
print("TEST 4: BRONZE TABLE VALIDATION")
print("=" * 60)

bronze_table = "main.ai_newsletter_bronze.tweets"

try:
    if not spark.catalog.tableExists(bronze_table):
        print(f"❌ FAIL: Bronze table does not exist: {bronze_table}")
        print("   Run: databricks bundle run ai_newsletter_bronze_job --profile DEFAULT")
    else:
        bronze_df = spark.sql(f"SELECT * FROM {bronze_table}")
        bronze_count = bronze_df.count()

        if bronze_count == 0:
            print(f"⚠️  WARNING: Bronze table exists but is empty")
            print("   The bronze processing job needs to run to ingest data from UC Volume")
        else:
            print(f"✅ PASS: Bronze table has {bronze_count} records")

            # Check for dummy vs real tweets
            dummy_count = bronze_df.filter("id LIKE 'dummy%'").count()
            real_count = bronze_count - dummy_count

            print(f"\n   📊 Data Breakdown:")
            print(f"   - Dummy tweets: {dummy_count}")
            print(f"   - Real tweets:  {real_count}")

            if real_count == 0:
                print("\n   ❌ FAIL: Bronze table only contains dummy data")
            else:
                print(f"\n   ✅ PASS: Bronze table contains {real_count} real tweets")

            # Show sample records
            print(f"\n   📄 Sample Records:")
            sample_df = bronze_df.orderBy("_commit_timestamp", ascending=False).limit(3)
            sample_df.select("id", "text", "author_id", "_commit_timestamp").show(truncate=60)

except Exception as e:
    print(f"❌ FAIL: Error accessing bronze table")
    print(f"   Error: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Data Freshness Check

# COMMAND ----------

print("=" * 60)
print("TEST 5: DATA FRESHNESS CHECK")
print("=" * 60)

try:
    # Check UC Volume freshness
    files = dbutils.fs.ls(raw_data_path)
    tweet_files = [f for f in files if f.name.startswith("tweet_") and f.name.endswith(".json")]

    if len(tweet_files) > 0:
        most_recent_file = max(tweet_files, key=lambda f: f.modificationTime)
        file_time = datetime.fromtimestamp(most_recent_file.modificationTime / 1000)
        age = datetime.now() - file_time

        print(f"Most recent file: {most_recent_file.name}")
        print(f"Created: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Age: {age.seconds // 60} minutes")

        # Job runs every 15 minutes, so data should be < 20 minutes old
        if age.seconds > 1200:  # 20 minutes
            print("\n⚠️  WARNING: Data is stale (>20 minutes old)")
            print("   Expected: Data refreshed every 15 minutes")
            print("   Check: Is the Twitter ingestion job running?")
        else:
            print("\n✅ PASS: Data is fresh (<20 minutes old)")

    # Check bronze table freshness
    if spark.catalog.tableExists(bronze_table):
        latest_record = spark.sql(f"""
            SELECT MAX(_commit_timestamp) as latest_commit
            FROM {bronze_table}
        """).collect()[0]

        if latest_record.latest_commit:
            age = datetime.now() - latest_record.latest_commit
            print(f"\nBronze table latest commit: {latest_record.latest_commit}")
            print(f"Age: {age.seconds // 60} minutes")

            # Bronze job runs hourly
            if age.seconds > 3900:  # 65 minutes
                print("⚠️  WARNING: Bronze data is stale (>65 minutes old)")
                print("   Expected: Bronze job runs hourly")
            else:
                print("✅ PASS: Bronze table is up to date")

except Exception as e:
    print(f"❌ Error checking data freshness: {e}")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Job Status Check

# COMMAND ----------

print("=" * 60)
print("TEST 6: JOB STATUS")
print("=" * 60)

print("To check job status via CLI:")
print()
print("# List jobs")
print("databricks jobs list --profile DEFAULT | grep -i twitter")
print()
print("# Check recent runs")
print("databricks jobs list-runs --limit 5 --profile DEFAULT | grep -i twitter")
print()
print("# View job in UI")
print("Databricks Workspace → Workflows → ai_newsletter_twitter_ingestion")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary and Recommendations

# COMMAND ----------

print("=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)
print()

# Provide recommendations based on findings
if not secret_configured:
    print("🔴 CRITICAL: Twitter API bearer token not configured")
    print()
    print("Action Required:")
    print("1. Verify you have a Twitter API bearer token")
    print("2. Store it in Databricks secrets:")
    print("   databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT")
    print("3. Redeploy and run the ingestion job:")
    print("   databricks bundle deploy --target default --profile DEFAULT")
    print("   databricks jobs run-now <JOB_ID> --profile DEFAULT")
    print()
else:
    print("✅ Bearer token configured")
    print()

    # Check if we're getting real data
    try:
        files = dbutils.fs.ls(raw_data_path)
        tweet_files = [f for f in files if f.name.startswith("tweet_") and f.name.endswith(".json")]
        real_count = sum(1 for f in tweet_files if "dummy" not in f.name)

        if real_count == 0:
            print("⚠️  WARNING: No real tweets being ingested")
            print()
            print("Possible Issues:")
            print("1. Twitter API token may be invalid or expired")
            print("2. Search terms may not be matching any tweets")
            print("3. API rate limits may be exceeded")
            print()
            print("Debugging Steps:")
            print("1. Check job logs in Databricks UI")
            print("2. Verify token is valid at developer.x.com")
            print("3. Test API manually with curl:")
            print('   curl -X GET "https://api.twitter.com/2/tweets/search/recent?query=databricks" \\')
            print('        -H "Authorization: Bearer YOUR_TOKEN"')
        else:
            print(f"✅ Successfully ingesting real Twitter data ({real_count} real tweets)")
            print()
            print("Next Steps:")
            print("1. Monitor bronze table for data flow")
            print("2. Verify silver processing with influence scores")
            print("3. Continue to T008: Gold daily materialized view")

    except:
        pass

print()
print("=" * 60)
