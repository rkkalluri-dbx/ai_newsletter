# Databricks notebook source
"""
Debug Twitter Ingestion - Check what's being fetched and filtered
"""

import requests
import json
from pyspark.sql import SparkSession
from datetime import datetime, timezone

# Configuration
bearer_token = dbutils.secrets.get(scope="ai_newsletter_config", key="twitter_bearer_token")
raw_data_path = "/Volumes/main/default/ai_newsletter_raw_tweets/"

# Bot Detection Configuration
BOT_DETECTION_ENABLED = True
BOT_MIN_ACCOUNT_AGE_DAYS = 30
BOT_MIN_FOLLOWERS = 10
BOT_MAX_FOLLOWING_RATIO = 10
BOT_KEYWORDS = ['bot', 'automated', 'auto-tweet', 'auto tweet', 'scheduled tweets']

# Twitter API
twitter_api_url = "https://api.twitter.com/2/tweets/search/recent"

# Get search terms
spark = SparkSession.builder.appName("debug_ingestion").getOrCreate()
search_terms_table = "main.config.search_terms"

search_terms = []
if spark.catalog.tableExists(search_terms_table):
    search_terms_df = spark.read.format("delta").table(search_terms_table)
    search_terms = [row.term for row in search_terms_df.filter("active = true").collect()]
    print(f"✅ Loaded {len(search_terms)} active search terms")
else:
    print("❌ No search terms table found")
    search_terms = ["Claude", "Databricks"]

query_string = " OR ".join(search_terms) + " lang:en -is:retweet"
print(f"\n🔍 Query string: {query_string}")
print(f"   Length: {len(query_string)} characters\n")

# Fetch tweets
headers = {
    "Authorization": f"Bearer {bearer_token}",
    "User-Agent": "DatabricksAISignalApp"
}

params = {
    "query": query_string,
    "tweet.fields": "author_id,public_metrics,created_at,lang",
    "expansions": "author_id",
    "user.fields": "created_at,public_metrics,verified,verified_type,description",
    "max_results": 100
}

print("=" * 80)
print("FETCHING TWEETS FROM TWITTER API")
print("=" * 80)

response = requests.get(twitter_api_url, headers=headers, params=params)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code} - {response.text}")
    dbutils.notebook.exit(f"API Error: {response.status_code}")

response_json = response.json()
tweets = response_json.get("data", [])
users = {user['id']: user for user in response_json.get("includes", {}).get("users", [])}

print(f"\n✅ Fetched {len(tweets)} tweets from Twitter API")

# Attach author metadata
for tweet in tweets:
    author_id = tweet.get('author_id')
    if author_id and author_id in users:
        tweet['author_metadata'] = users[author_id]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Analyze Tweets

# COMMAND ----------

print("=" * 80)
print("ANALYZING FETCHED TWEETS")
print("=" * 80)

if not tweets:
    print("\n⚠️  NO TWEETS FETCHED FROM API")
    print("   This could mean:")
    print("   1. No recent tweets match your search terms")
    print("   2. Twitter API rate limit reached")
    print("   3. Search terms are too specific")
    dbutils.notebook.exit("No tweets to analyze")

# Analyze each tweet
lang_issues = 0
bot_issues = 0
valid_tweets = 0

print(f"\nAnalyzing {len(tweets)} tweets:\n")

for i, tweet in enumerate(tweets[:10], 1):  # Show first 10
    tweet_id = tweet.get('id')
    tweet_lang = tweet.get('lang', 'en')
    author = tweet.get('author_metadata', {})

    print(f"Tweet #{i} (ID: {tweet_id}):")
    print(f"  Language: {tweet_lang}")

    # Check language
    lang_ok = tweet_lang == 'en'
    print(f"  Lang filter: {'✅ PASS' if lang_ok else '❌ FAIL (not English)'}")

    if not lang_ok:
        lang_issues += 1
        print()
        continue

    # Check bot
    if author:
        username = author.get('username', 'unknown')
        verified = author.get('verified', False)
        metrics = author.get('public_metrics', {})
        followers = metrics.get('followers_count', 0)
        following = metrics.get('following_count', 0)
        created_at = author.get('created_at', '')

        print(f"  Author: @{username}")
        print(f"  Verified: {verified}")
        print(f"  Followers: {followers}")
        print(f"  Following: {following}")

        # Calculate account age
        account_age = "unknown"
        if created_at:
            try:
                account_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age_days = (datetime.now(timezone.utc) - account_created).days
                account_age = f"{account_age_days} days"
                print(f"  Account age: {account_age}")
            except:
                pass

        # Bot checks
        bot_reasons = []

        if verified or author.get('verified_type') in ['blue', 'business', 'government']:
            print(f"  Bot check: ✅ PASS (verified account)")
            valid_tweets += 1
        else:
            # Check age
            if created_at:
                try:
                    account_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    account_age_days = (datetime.now(timezone.utc) - account_created).days
                    if account_age_days < BOT_MIN_ACCOUNT_AGE_DAYS:
                        bot_reasons.append(f"account age {account_age_days} < {BOT_MIN_ACCOUNT_AGE_DAYS} days")
                except:
                    pass

            # Check followers
            if followers < BOT_MIN_FOLLOWERS:
                bot_reasons.append(f"followers {followers} < {BOT_MIN_FOLLOWERS}")

            # Check ratio
            if following > 100 and followers > 0:
                ratio = following / followers
                if ratio > BOT_MAX_FOLLOWING_RATIO:
                    bot_reasons.append(f"following/followers ratio {ratio:.1f} > {BOT_MAX_FOLLOWING_RATIO}")

            if bot_reasons:
                print(f"  Bot check: ❌ FAIL - {', '.join(bot_reasons)}")
                bot_issues += 1
            else:
                print(f"  Bot check: ✅ PASS")
                valid_tweets += 1
    else:
        print(f"  Author: No metadata")
        print(f"  Bot check: ✅ PASS (no author data, allow by default)")
        valid_tweets += 1

    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("=" * 80)
print("FILTERING SUMMARY")
print("=" * 80)
print(f"Total fetched: {len(tweets)} tweets")
print(f"Language issues: {lang_issues} tweets")
print(f"Bot issues: {bot_issues} tweets")
print(f"Valid tweets: {valid_tweets} tweets")
print(f"\nWould land: {valid_tweets}/{len(tweets)} tweets ({valid_tweets*100//len(tweets) if tweets else 0}%)")

if valid_tweets == 0:
    print("\n⚠️  WARNING: ALL TWEETS FILTERED OUT!")
    print("\nRecommendations:")
    print("1. Lower bot detection thresholds:")
    print(f"   - BOT_MIN_FOLLOWERS (currently {BOT_MIN_FOLLOWERS}) → Try 5")
    print(f"   - BOT_MIN_ACCOUNT_AGE_DAYS (currently {BOT_MIN_ACCOUNT_AGE_DAYS}) → Try 7")
    print("2. Or disable bot detection temporarily:")
    print("   - Set BOT_DETECTION_ENABLED = False")

print("=" * 80)
