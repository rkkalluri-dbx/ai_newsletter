# Databricks notebook source
# MAGIC %md
# MAGIC # Twitter Token Diagnostic
# MAGIC
# MAGIC This notebook tests the Twitter bearer token configuration and API connectivity.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Retrieve Secret

# COMMAND ----------

import requests
import json

print("=" * 60)
print("STEP 1: SECRET RETRIEVAL")
print("=" * 60)

try:
    bearer_token = dbutils.secrets.get(scope="ai_newsletter_config", key="twitter_bearer_token")

    # Check token format
    token_length = len(bearer_token)
    token_prefix = bearer_token[:10] if len(bearer_token) >= 10 else bearer_token

    print(f"✅ Secret retrieved successfully")
    print(f"   Length: {token_length} characters")
    print(f"   Prefix: {token_prefix}...")

    # Check if it's a placeholder
    if bearer_token == "YOUR_TWITTER_BEARER_TOKEN_HERE":
        print("\n❌ ERROR: Token is the placeholder value")
        print("   Action: Update the secret with a real Twitter bearer token")
        is_placeholder = True
    elif token_length < 50:
        print(f"\n⚠️  WARNING: Token seems too short ({token_length} chars)")
        print("   Twitter bearer tokens are typically 100+ characters")
        is_placeholder = False
    else:
        print(f"\n✅ Token format looks valid ({token_length} chars)")
        is_placeholder = False

except Exception as e:
    print(f"❌ ERROR: Could not retrieve secret")
    print(f"   Error: {e}")
    bearer_token = None
    is_placeholder = True

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Test Twitter API Connection

# COMMAND ----------

if bearer_token and not is_placeholder:
    print("=" * 60)
    print("STEP 2: TWITTER API TEST")
    print("=" * 60)

    # Simple test query
    test_url = "https://api.twitter.com/2/tweets/search/recent"
    test_params = {
        "query": "databricks",
        "max_results": 10
    }
    test_headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "DatabricksAISignalApp"
    }

    print(f"Testing API endpoint: {test_url}")
    print(f"Query: {test_params['query']}")
    print()

    try:
        response = requests.get(test_url, headers=test_headers, params=test_params, timeout=10)

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("✅ SUCCESS: API call successful")
            data = response.json()

            tweet_count = len(data.get("data", []))
            print(f"   Retrieved {tweet_count} tweets")

            if tweet_count > 0:
                print("\n   Sample tweet:")
                sample_tweet = data["data"][0]
                print(f"   - ID: {sample_tweet.get('id')}")
                print(f"   - Text: {sample_tweet.get('text', '')[:80]}...")

            # Show rate limit info
            if "x-rate-limit-remaining" in response.headers:
                print(f"\n   Rate Limit Info:")
                print(f"   - Remaining: {response.headers.get('x-rate-limit-remaining')}")
                print(f"   - Limit: {response.headers.get('x-rate-limit-limit')}")
                print(f"   - Reset: {response.headers.get('x-rate-limit-reset')}")

        elif response.status_code == 401:
            print("❌ ERROR: 401 Unauthorized")
            print("   Your bearer token is invalid or expired")
            print()
            print("   Actions:")
            print("   1. Go to https://developer.x.com/en/portal/projects-and-apps")
            print("   2. Navigate to your app → Keys and Tokens")
            print("   3. Regenerate Bearer Token")
            print("   4. Update Databricks secret:")
            print("      databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT")

        elif response.status_code == 403:
            print("❌ ERROR: 403 Forbidden")
            print("   Your app doesn't have the required access level")
            print()
            response_data = response.json()
            print(f"   API Response: {json.dumps(response_data, indent=2)}")

        elif response.status_code == 429:
            print("❌ ERROR: 429 Rate Limit Exceeded")
            print("   You've exceeded your API rate limits")
            print()
            print("   Solutions:")
            print("   1. Wait for rate limit to reset")
            print("   2. Reduce ingestion frequency")
            print("   3. Upgrade to higher API tier")

        else:
            print(f"❌ ERROR: Unexpected status code {response.status_code}")
            print()
            print("   Response:")
            try:
                print(f"   {json.dumps(response.json(), indent=2)}")
            except:
                print(f"   {response.text[:500]}")

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timeout")
        print("   API took too long to respond")

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Connection error")
        print("   Could not connect to Twitter API")
        print("   Check network connectivity")

    except Exception as e:
        print(f"❌ ERROR: Unexpected error during API call")
        print(f"   Error: {e}")

else:
    print("=" * 60)
    print("SKIPPING API TEST")
    print("=" * 60)
    print("Cannot test API - token is placeholder or not configured")

print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Test Full Query with Search Terms

# COMMAND ----------

if bearer_token and not is_placeholder:
    print("=" * 60)
    print("STEP 3: FULL QUERY TEST")
    print("=" * 60)

    # Get search terms from config or use defaults
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()

    catalog_name = spark.sql("SELECT current_catalog()").collect()[0][0]
    search_terms_table = f"{catalog_name}.config.search_terms"

    search_terms = []
    try:
        if spark.catalog.tableExists(search_terms_table):
            search_terms_df = spark.read.format("delta").table(search_terms_table)
            search_terms = [row.term for row in search_terms_df.collect()]
    except:
        pass

    if not search_terms:
        search_terms = ["Gemini", "Databricks", "Claude Code", "Claude", "AI Driven Development"]

    query_string = " OR ".join(search_terms) + " lang:en -is:retweet"

    print(f"Search Terms: {', '.join(search_terms)}")
    print(f"Query: {query_string}")
    print()

    full_params = {
        "query": query_string,
        "tweet.fields": "author_id,public_metrics,created_at",
        "max_results": 100
    }

    full_headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "DatabricksAISignalApp"
    }

    try:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=full_headers,
            params=full_params,
            timeout=15
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            tweets = data.get("data", [])

            print(f"✅ SUCCESS: Retrieved {len(tweets)} tweets")

            if len(tweets) > 0:
                print("\n   Sample Tweets:")
                for i, tweet in enumerate(tweets[:3], 1):
                    print(f"\n   Tweet {i}:")
                    print(f"   - ID: {tweet.get('id')}")
                    print(f"   - Text: {tweet.get('text', '')[:80]}...")
                    metrics = tweet.get('public_metrics', {})
                    print(f"   - Likes: {metrics.get('like_count', 0)}, Retweets: {metrics.get('retweet_count', 0)}")
            else:
                print("\n   ⚠️  No tweets matched the search criteria")
                print("   This could mean:")
                print("   - No recent tweets match your search terms")
                print("   - Search terms are too specific")

        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                print(f"   {json.dumps(response.json(), indent=2)}")
            except:
                print(f"   {response.text[:500]}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary & Recommendations

# COMMAND ----------

print("=" * 60)
print("DIAGNOSTIC SUMMARY")
print("=" * 60)
print()

if bearer_token is None:
    print("🔴 CRITICAL: Secret not configured")
    print()
    print("Run this command:")
    print("databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT")

elif is_placeholder:
    print("🔴 CRITICAL: Token is placeholder value")
    print()
    print("Run this command with your real token:")
    print("databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT")

else:
    print("Based on the API test results above:")
    print()
    print("If API test was successful (200 OK):")
    print("  → Token is valid and working")
    print("  → Check ingestion script for errors")
    print("  → Review job logs in Databricks UI")
    print()
    print("If API test failed (401):")
    print("  → Regenerate token at developer.x.com")
    print("  → Update secret with new token")
    print()
    print("If API test failed (429):")
    print("  → Rate limit exceeded")
    print("  → Reduce ingestion frequency")
    print("  → Consider upgrading API tier")
    print()
    print("If API test failed (403):")
    print("  → Check API access level")
    print("  → Verify app permissions")

print()
print("=" * 60)
