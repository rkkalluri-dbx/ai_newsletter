# Databricks notebook source
import requests
import json
import time
from pyspark.sql import SparkSession

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

# Twitter API endpoint for recent search (v2)
twitter_api_url = "https://api.twitter.com/2/tweets/search/recent"

# --- Search terms from the config Delta table (T002) ---
# Initialize Spark Session (if not already initialized by Databricks)
spark = SparkSession.builder.appName("twitter_ingestion_job").getOrCreate()

# Retrieve search terms from the Delta table
try:
    catalog_name = spark.sql("SELECT current_catalog()").collect()[0][0]
except Exception:
    catalog_name = "hive_metastore" # Fallback if current_catalog() fails
schema_name = "config"
search_terms_table = f"{catalog_name}.{schema_name}.search_terms"

# Ensure the schema exists before trying to read from it
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

search_terms = []
try:
    # Check if table exists before reading
    if spark.catalog.tableExists(search_terms_table):
        search_terms_df = spark.read.format("delta").table(search_terms_table)
        search_terms = [row.term for row in search_terms_df.collect()]
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
    "tweet.fields": "author_id,public_metrics,created_at",
    "max_results": 100 # Max results per request
}

def fetch_tweets():
    """Fetches tweets from Twitter API and lands them as JSON files."""
    print(f"Fetching tweets with query: {query_string}")
    response = requests.get(twitter_api_url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching tweets: {response.status_code} - {response.text}")
        return []

    data = response.json().get("data", [])
    tweets = data if isinstance(data, list) else [] # Ensure data is a list
    print(f"Fetched {len(tweets)} tweets.")
    return tweets

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

    for tweet in tweets_data:
        file_name = f"{raw_data_path}tweet_{tweet['id']}_{int(time.time())}.json" # Add timestamp to avoid overwrites
        dbutils.fs.put(file_name, json.dumps(tweet), overwrite=True)
        print(f"Landed tweet {tweet['id']} to {file_name}")

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
        print(f"📡 Calling Twitter API...")
        tweets = fetch_tweets()
        if tweets:
            print(f"📥 Landing {len(tweets)} real tweets...")
            land_tweets(tweets)
        else:
            print("⚠️  No tweets fetched or an error occurred. No data landed.")