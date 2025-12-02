# Databricks notebook source
import requests
import json
import time
from pyspark.sql import SparkSession
from datetime import datetime, timezone

# --- Configuration ---
# NOTE: The Twitter bearer token should be stored in a Databricks secret scope.
# For example, to access a secret in scope 'my_scope' with key 'twitter_bearer_token':
#bearer_token = dbutils.secrets.get(scope="ai_newsletter_config", key="twitter_bearer_token")

# For local testing or if secrets are not configured yet, use a placeholder.
# IMPORTANT: DO NOT hardcode secrets in your notebooks.
BEARER_TOKEN_PLACEHOLDER = "YOUR_TWITTER_BEARER_TOKEN_HERE"

# If running in Databricks, retrieve secret. Otherwise, use placeholder.
try:
    # This assumes a secret scope and key are configured in Databricks.
    # Replace "your_scope_name" and "twitter_bearer_token" with actual values.
    # For now, we'll use a placeholder if not found.
    #bearer_token = BEARER_TOKEN_PLACEHOLDER
    bearer_token = dbutils.secrets.get(scope="ai_newsletter_config", key="twitter_bearer_token")
    print(f"✅ Successfully retrieved bearer token (length: {len(bearer_token)} chars)")
except Exception as e:
    print(f"❌ ERROR retrieving secret: {e}")
    bearer_token = BEARER_TOKEN_PLACEHOLDER

# Path where raw tweets will be landed (bronze layer source)
# Changed from DBFS /tmp path to a Unity Catalog volume path
raw_data_path = "/Volumes/main/default/ai_newsletter_raw_tweets/"

# Bot Detection Configuration (adjust thresholds as needed)
BOT_DETECTION_ENABLED = True
BOT_MIN_ACCOUNT_AGE_DAYS = 30      # Accounts newer than this are suspicious
BOT_MIN_FOLLOWERS = 10              # Accounts with fewer followers are suspicious
BOT_MAX_FOLLOWING_RATIO = 10        # Following/Followers ratio threshold (10:1)
BOT_KEYWORDS = ['bot', 'automated', 'auto-tweet', 'auto tweet', 'scheduled tweets']

# Twitter API endpoint for recent search (v2)
twitter_api_url = "https://api.twitter.com/2/tweets/search/recent"

# --- Search terms from the config Delta table (T002) ---
# Initialize Spark Session (if not already initialized by Databricks)
spark = SparkSession.builder.appName("twitter_ingestion_job").getOrCreate()

# Retrieve search terms from the Delta table
# Explicitly use 'main' catalog for consistency
catalog_name = "main"
schema_name = "config"
search_terms_table = f"{catalog_name}.{schema_name}.search_terms"

# Ensure the schema exists before trying to read from it
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

search_terms = []
try:
    # Check if table exists before reading
    if spark.catalog.tableExists(search_terms_table):
        search_terms_df = spark.read.format("delta").table(search_terms_table)
        # Only use active search terms
        search_terms = [row.term for row in search_terms_df.filter("active = true").collect()]
        print(f"✅ Loaded {len(search_terms)} active search terms from {search_terms_table}")
    else:
        print(f"Table {search_terms_table} does not exist. Using default search terms.")
except Exception as e:
    print(f"Could not read search terms from {search_terms_table}: {e}")
    print("Falling back to default search terms.")
    
if not search_terms:
    print("No search terms found in config table, using default terms.")
    search_terms = ["Gemini", "Databricks", "Claude Code", "Claude","AI Driven Development"] # Default terms if table not found

query_string = " OR ".join(search_terms) + " lang:en -is:retweet" # Exclude retweets

# --- Twitter API Call ---
headers = {
    "Authorization": f"Bearer {bearer_token}",
    "User-Agent": "DatabricksAISignalApp"
}

params = {
    "query": query_string,
    "tweet.fields": "author_id,public_metrics,created_at,lang",
    "expansions": "author_id",  # Get author details
    "user.fields": "created_at,public_metrics,verified,verified_type,description",  # Author metadata for bot detection
    "max_results": 100
}

# --- Watermark Management ---
WATERMARK_TABLE = "main.config.twitter_ingestion_watermark"
JOB_NAME = "twitter_ingestion"

def create_watermark_table():
    """Create watermark table if it doesn't exist"""
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS main.config")

    if not spark.catalog.tableExists(WATERMARK_TABLE):
        print(f"Creating watermark table: {WATERMARK_TABLE}")
        spark.sql(f"""
            CREATE TABLE {WATERMARK_TABLE} (
                job_name STRING NOT NULL,
                last_ingestion_time TIMESTAMP NOT NULL,
                last_tweet_id STRING,
                tweets_fetched INT,
                updated_at TIMESTAMP NOT NULL
            ) USING DELTA
        """)
        print(f"✅ Watermark table created")

def get_last_watermark():
    """Get the last ingestion timestamp for resuming"""
    create_watermark_table()

    try:
        watermark_df = spark.read.format("delta").table(WATERMARK_TABLE)
        watermark_row = watermark_df.filter(f"job_name = '{JOB_NAME}'").orderBy("updated_at", ascending=False).first()

        if watermark_row:
            last_time = watermark_row['last_ingestion_time']
            last_tweet_id = watermark_row['last_tweet_id']
            print(f"📍 Last watermark: {last_time} (tweet ID: {last_tweet_id})")
            return last_time, last_tweet_id
        else:
            print(f"📍 No previous watermark found - first run, fetching last 2 hours")
            return None, None
    except Exception as e:
        print(f"⚠️  Error reading watermark: {e}")
        return None, None

def update_watermark(ingestion_time, last_tweet_id, tweets_count):
    """Update the watermark after successful ingestion"""
    from delta.tables import DeltaTable

    create_watermark_table()
    print(f"💾 Updating watermark: {ingestion_time} (tweet ID: {last_tweet_id}, count: {tweets_count})")

    # Create new watermark record
    new_watermark_data = [(JOB_NAME, ingestion_time, last_tweet_id, tweets_count, datetime.now(timezone.utc))]
    new_watermark = spark.createDataFrame(new_watermark_data, ["job_name", "last_ingestion_time", "last_tweet_id", "tweets_fetched", "updated_at"])

    # Upsert watermark
    delta_table = DeltaTable.forName(spark, WATERMARK_TABLE)
    delta_table.alias("existing") \
        .merge(new_watermark.alias("updates"), "existing.job_name = updates.job_name") \
        .whenMatchedUpdateAll() \
        .whenNotMatchedInsertAll() \
        .execute()

    print(f"✅ Watermark updated successfully")

def fetch_tweets(start_time=None):
    """Fetches tweets from Twitter API with pagination and watermarking."""
    print(f"Fetching tweets with query: {query_string}")

    if start_time:
        # Format datetime for Twitter API (ISO 8601)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"📍 Resuming from watermark: {start_time_str}")
    else:
        print(f"📍 No watermark - fetching recent tweets")

    all_tweets = []
    all_users = {}
    next_token = None
    page = 0
    max_pages = 5  # Limit to 5 pages (500 tweets max) to avoid excessive API calls

    while page < max_pages:
        page += 1

        # Add pagination token and start_time if available
        current_params = params.copy()
        if next_token:
            current_params["pagination_token"] = next_token
        if start_time:
            current_params["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"  Fetching page {page}...")
        response = requests.get(twitter_api_url, headers=headers, params=current_params)

        if response.status_code == 429:
            error_msg = f"❌ Twitter API Rate Limit Exceeded (429): {response.text}"
            print(error_msg)
            raise Exception(error_msg)

        if response.status_code != 200:
            print(f"Error fetching tweets (page {page}): {response.status_code} - {response.text}")
            break

        response_json = response.json()
        tweets = response_json.get("data", [])

        if not isinstance(tweets, list) or len(tweets) == 0:
            print(f"  No more tweets found on page {page}")
            break

        # Collect tweets
        all_tweets.extend(tweets)

        # Collect users from this page
        page_users = {user['id']: user for user in response_json.get("includes", {}).get("users", [])}
        all_users.update(page_users)

        print(f"  Fetched {len(tweets)} tweets (total so far: {len(all_tweets)})")

        # Check for next page
        meta = response_json.get("meta", {})
        next_token = meta.get("next_token")

        if not next_token:
            print(f"  No more pages available")
            break

    # Attach author metadata to all tweets
    for tweet in all_tweets:
        author_id = tweet.get('author_id')
        if author_id and author_id in all_users:
            tweet['author_metadata'] = all_users[author_id]

    print(f"✅ Fetched {len(all_tweets)} total tweets across {page} page(s)")
    return all_tweets

def is_likely_bot(tweet):
    """
    Heuristic bot detection based on author metadata.

    Returns True if the tweet is likely from a bot, False if likely human.

    Bot indicators (configurable via constants):
    - Very new account (< BOT_MIN_ACCOUNT_AGE_DAYS)
    - Very low followers (< BOT_MIN_FOLLOWERS)
    - Suspicious follower/following ratio (> BOT_MAX_FOLLOWING_RATIO)
    - Bot keywords in bio (BOT_KEYWORDS)
    """
    # If bot detection is disabled, allow all tweets
    if not BOT_DETECTION_ENABLED:
        return False

    author = tweet.get('author_metadata', {})

    # If no author metadata, be conservative and allow the tweet
    if not author:
        return False

    # Verified accounts are typically not bots (strong signal)
    if author.get('verified', False) or author.get('verified_type') in ['blue', 'business', 'government']:
        return False

    # Check account age
    created_at = author.get('created_at')
    if created_at:
        try:
            from datetime import datetime, timezone
            account_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            account_age_days = (datetime.now(timezone.utc) - account_created).days

            # Very new accounts are often bots
            if account_age_days < BOT_MIN_ACCOUNT_AGE_DAYS:
                return True
        except:
            pass  # If date parsing fails, skip this check

    # Check follower metrics
    metrics = author.get('public_metrics', {})
    followers = metrics.get('followers_count', 0)
    following = metrics.get('following_count', 0)

    # Very low follower count suggests bot
    if followers < BOT_MIN_FOLLOWERS:
        return True

    # Suspicious follower ratios (following way more than followers)
    if following > 100 and followers > 0:
        ratio = following / followers
        if ratio > BOT_MAX_FOLLOWING_RATIO:
            return True

    # Check for bot keywords in description
    description = author.get('description', '').lower()
    if any(keyword in description for keyword in BOT_KEYWORDS):
        return True

    # Default: assume human
    return False

def land_tweets(tweets_data):
    """Writes fetched tweets to raw data path as JSON files."""
    # dbutils.fs.mkdirs(raw_data_path) # dbutils.fs.mkdirs is not needed for UC Volumes
    # Ensure the parent directories for the volume exist. This is usually managed by UC volumes.
    # For a barebones example, we'll assume the volume path is correctly configured.

    # Check if the path exists, if not, it means the volume might not be properly set up or accessible.
    try:
        dbutils.fs.ls(raw_data_path)
    except Exception as e:
        print(f"Warning: Raw data path {raw_data_path} might not exist or be accessible: {e}")
        print("Please ensure your Unity Catalog volume is correctly configured and mounted/accessible.")
        # Attempt to create the directory anyway, in case it's a permission issue not existence
        # dbutils.fs.mkdirs(raw_data_path) # Still use for robustness if UC volume doesn't auto-create sub-paths

    landed_count = 0
    filtered_lang = 0
    filtered_bot = 0
    newest_tweet_time = None
    newest_tweet_id = None

    for tweet in tweets_data:
        # Filter 1: Language check (safety check in case API filter missed some)
        tweet_lang = tweet.get('lang', 'en')  # Default to 'en' if lang field missing

        if tweet_lang != 'en':
            filtered_lang += 1
            print(f"⚠️  Filtered out non-English tweet {tweet['id']} (lang: {tweet_lang})")
            continue

        # Filter 2: Bot detection
        if is_likely_bot(tweet):
            filtered_bot += 1
            author = tweet.get('author_metadata', {})
            author_name = author.get('username', 'unknown')
            followers = author.get('public_metrics', {}).get('followers_count', 0)
            print(f"🤖 Filtered out likely bot tweet {tweet['id']} (author: @{author_name}, followers: {followers})")
            continue

        file_name = f"{raw_data_path}tweet_{tweet['id']}_{int(time.time())}.json" # Add timestamp to avoid overwrites
        dbutils.fs.put(file_name, json.dumps(tweet), overwrite=True)
        landed_count += 1
        print(f"✅ Landed tweet {tweet['id']} to {file_name}")

        # Track the newest tweet for watermarking
        tweet_created_at = tweet.get('created_at')
        if tweet_created_at:
            try:
                tweet_time = datetime.strptime(tweet_created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                if newest_tweet_time is None or tweet_time > newest_tweet_time:
                    newest_tweet_time = tweet_time
                    newest_tweet_id = tweet['id']
            except:
                pass  # Skip if datetime parsing fails

    # Summary
    print(f"\n{'='*60}")
    print(f"INGESTION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Landed: {landed_count} tweets from humans")
    print(f"⚠️  Filtered (language): {filtered_lang} tweets")
    print(f"🤖 Filtered (bots): {filtered_bot} tweets")
    print(f"Total fetched: {len(tweets_data)} tweets")
    print(f"{'='*60}")

    # Update watermark if tweets were landed
    if landed_count > 0 and newest_tweet_time:
        update_watermark(newest_tweet_time, newest_tweet_id, landed_count)

    return landed_count

# --- Main Execution ---
if __name__ == "__main__":
    print(f"🔍 Checking bearer token... (placeholder: {BEARER_TOKEN_PLACEHOLDER[:10]}...)")
    print(f"🔍 Current token: {bearer_token[:10]}...")

    if bearer_token == BEARER_TOKEN_PLACEHOLDER:
        print("⚠️  WARNING: Bearer token is a placeholder. Please configure Databricks secrets.")
        print("📝 Simulating tweet fetching and landing with dummy data.")
        # Simulate fetching and landing for demonstration if token is not set up
        dummy_tweets = [
            {'id': 'dummy_1', 'text': 'Dummy tweet about AI.', 'public_metrics': {'like_count': 15, 'retweet_count': 2, 'reply_count': 1, 'quote_count': 0}, 'author_id': 'user_A', 'created_at': '2023-01-01T10:00:00Z'},
            {'id': 'dummy_2', 'text': 'Dummy tweet about Databricks.', 'public_metrics': {'like_count': 5, 'retweet_count': 0, 'reply_count': 0, 'quote_count': 0}, 'author_id': 'user_B', 'created_at': '2023-01-01T10:05:00Z'},
            {'id': 'dummy_3', 'text': 'Dummy tweet about LLM.', 'public_metrics': {'like_count': 20, 'retweet_count': 5, 'reply_count': 2, 'quote_count': 1}, 'author_id': 'user_C', 'created_at': '2023-01-01T10:10:00Z'},
        ]
        land_tweets(dummy_tweets)
    else:
        print("✅ Using real Twitter bearer token")

        # Get last watermark to resume from
        last_watermark_time, last_watermark_id = get_last_watermark()

        print(f"📡 Calling Twitter API...")
        tweets = fetch_tweets(start_time=last_watermark_time)

        if tweets:
            print(f"📥 Landing {len(tweets)} real tweets...")
            land_tweets(tweets)
        else:
            print("⚠️  No tweets fetched or an error occurred. No data landed.")