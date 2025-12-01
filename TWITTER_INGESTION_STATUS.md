# Twitter Ingestion Status - AI Newsletter

Current status of Twitter feed ingestion implementation for the AI Newsletter project.

## 📊 Current Implementation Overview

### Architecture
```
Twitter API v2 (Recent Search)
    ↓
Bearer Token Authentication
    ↓
Search Terms (from config.search_terms table)
    ↓
JSON Files → Unity Catalog Volume
    ↓
Bronze Delta Table (Auto Loader)
    ↓
Silver Delta Table (Deduplication + Scoring)
```

### Implementation Details

**File:** `src/twitter_ingestion_script.py`
**Job:** `ai_newsletter_twitter_ingestion`
**Schedule:** Every 15 minutes (cron: `0 */15 * * * ?`)

## 🔧 How It Works

### 1. Configuration

**Search Terms Source:**
- Primary: `config.search_terms` Delta table
- Fallback: Default terms ["AI", "Databricks", "LLM", "Machine Learning"]

**Storage Location:**
- Unity Catalog Volume: `/Volumes/main/default/ai_newsletter_raw_tweets/`

**Authentication:**
- Method: Bearer token authentication
- Current Status: ⚠️ **PLACEHOLDER** - needs actual token
- Expected Source: Databricks secrets

### 2. API Request

**Endpoint:**
```
https://api.twitter.com/2/tweets/search/recent
```

**Query Parameters:**
```python
{
    "query": "AI OR Databricks OR LLM OR Machine Learning lang:en -is:retweet",
    "tweet.fields": "author_id,public_metrics,created_at",
    "max_results": 100
}
```

**Headers:**
```python
{
    "Authorization": f"Bearer {bearer_token}",
    "User-Agent": "DatabricksAISignalApp"
}
```

### 3. Data Capture

**Fields Retrieved:**
- `id` - Tweet ID
- `text` - Tweet text content
- `author_id` - Author user ID
- `public_metrics` - Engagement metrics object:
  - `like_count`
  - `retweet_count`
  - `reply_count`
  - `quote_count`
- `created_at` - Tweet timestamp

### 4. Data Landing

**Method:** Individual JSON files per tweet
**File Format:** `tweet_{tweet_id}_{timestamp}.json`
**Location:** Unity Catalog Volume

Example file:
```json
{
  "id": "1234567890",
  "text": "Excited about the new AI developments...",
  "author_id": "987654321",
  "public_metrics": {
    "like_count": 15,
    "retweet_count": 2,
    "reply_count": 1,
    "quote_count": 0
  },
  "created_at": "2023-01-01T10:00:00Z"
}
```

## ⚠️ Current Limitations & TODOs

### 1. Authentication (Critical)
**Status:** ❌ Not Configured

```python
# Current (line 21-22):
bearer_token = BEARER_TOKEN_PLACEHOLDER

# Needed:
bearer_token = dbutils.secrets.get(scope="ai_newsletter", key="twitter_bearer_token")
```

**Action Required:**
```bash
# 1. Create secret scope
databricks secrets create-scope ai_newsletter --profile DEFAULT

# 2. Store Twitter bearer token
databricks secrets put-secret ai_newsletter twitter_bearer_token --profile DEFAULT

# 3. Update twitter_ingestion_script.py line 22
```

**Without this:** Currently using dummy data (3 fake tweets)

### 2. Missing Language Field
**Status:** ⚠️ Not Captured

**Current:** Query filters for `lang:en` but field not returned
**Impact:** Silver table can't verify English language
**Solution:** Add `lang` to tweet.fields

```python
# Update line 74:
params = {
    "query": query_string,
    "tweet.fields": "author_id,public_metrics,created_at,lang",  # Add lang
    "max_results": 100
}
```

### 3. Missing Author Metadata
**Status:** ⚠️ Not Captured

**Current:** Only `author_id` is captured
**Missing:**
- Author name/username
- Follower count
- Verified status

**Impact:** Silver table has placeholder values for enrichment

**Solution:** Add user expansion to API request

```python
# Update params (line 72-76):
params = {
    "query": query_string,
    "tweet.fields": "author_id,public_metrics,created_at,lang",
    "expansions": "author_id",  # Add this
    "user.fields": "name,username,public_metrics,verified",  # Add this
    "max_results": 100
}

# Then extract user data from response.includes.users
```

### 4. Pagination Not Implemented
**Status:** ⚠️ Limited to 100 tweets

**Current:** Single request, max 100 tweets per run
**Impact:** May miss tweets if >100 match in 15 minutes
**Solution:** Implement pagination using `next_token`

```python
def fetch_tweets_paginated(max_pages=5):
    all_tweets = []
    next_token = None

    for page in range(max_pages):
        params = {...}
        if next_token:
            params["next_token"] = next_token

        response = requests.get(twitter_api_url, headers=headers, params=params)
        data = response.json()

        all_tweets.extend(data.get("data", []))
        next_token = data.get("meta", {}).get("next_token")

        if not next_token:
            break

    return all_tweets
```

### 5. Rate Limiting Not Handled
**Status:** ⚠️ No retry logic

**Risk:** Job may fail if rate limits hit
**Solution:** Add retry with exponential backoff

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def fetch_tweets_with_retry():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    response = session.get(twitter_api_url, headers=headers, params=params)
    return response
```

### 6. Search Terms Table Not Created
**Status:** ⚠️ Table doesn't exist yet

**Current:** Using fallback default terms
**Impact:** Can't customize search terms without code changes

**Action Required:**
```sql
-- Create config schema and table
CREATE SCHEMA IF NOT EXISTS main.config;

CREATE TABLE IF NOT EXISTS main.config.search_terms (
  term STRING,
  active BOOLEAN DEFAULT true,
  added_date TIMESTAMP DEFAULT current_timestamp()
);

-- Insert search terms
INSERT INTO main.config.search_terms (term) VALUES
  ('claude'),
  ('databricks'),
  ('gemini'),
  ('openai'),
  ('LLM'),
  ('machine learning'),
  ('artificial intelligence');
```

## 📈 Current Data Flow

### Scenario: Job Runs Every 15 Minutes

**With Actual Token:**
```
1. Job triggers (15-min schedule)
2. Read search terms from config.search_terms table
3. Build query: "term1 OR term2 OR ... lang:en -is:retweet"
4. Call Twitter API with Bearer token
5. Fetch up to 100 tweets
6. Write each tweet as JSON file to UC Volume
7. Bronze job picks up files via Auto Loader
8. Silver job processes with deduplication + scoring
```

**Currently (No Token):**
```
1. Job triggers
2. Detects placeholder token
3. Uses 3 dummy tweets
4. Writes dummy data to UC Volume
5. Bronze and silver process dummy data
```

## 🎯 Priority Improvements

### High Priority (Blocking Production)

1. **Configure Twitter API Bearer Token** (T019 related)
   - Create secret scope
   - Store bearer token
   - Update ingestion script

2. **Create Search Terms Table**
   - Run SQL to create config.search_terms
   - Populate with target keywords

### Medium Priority (Affects Data Quality)

3. **Add Language Field**
   - Update API request to include lang field
   - Update bronze schema

4. **Add Author Metadata**
   - Update API request with user expansion
   - Extract author details from response
   - Update bronze schema

### Low Priority (Performance/Scalability)

5. **Implement Pagination**
   - Handle next_token for >100 tweets
   - Set reasonable page limit

6. **Add Rate Limit Handling**
   - Implement retry logic
   - Add exponential backoff

7. **Error Monitoring**
   - Log failed API calls
   - Alert on consecutive failures

## 🔍 How to Verify Current Status

### Check if Job is Running

```bash
# List jobs
databricks jobs list --profile DEFAULT | grep twitter_ingestion

# Check recent runs
databricks jobs list-runs --job-name ai_newsletter_twitter_ingestion --profile DEFAULT
```

### Check Data in UC Volume

```python
# In Databricks notebook
dbutils.fs.ls("/Volumes/main/default/ai_newsletter_raw_tweets/")

# Count files
len(dbutils.fs.ls("/Volumes/main/default/ai_newsletter_raw_tweets/"))

# Read sample file
sample_file = dbutils.fs.ls("/Volumes/main/default/ai_newsletter_raw_tweets/")[0].path
print(dbutils.fs.head(sample_file))
```

### Check Bronze Table

```sql
-- Check if data is flowing
SELECT COUNT(*) as tweet_count
FROM main.ai_newsletter_bronze.tweets;

-- View sample tweets
SELECT id, text, public_metrics.like_count, author_id
FROM main.ai_newsletter_bronze.tweets
LIMIT 10;
```

## 🚀 Next Steps to Enable Real Twitter Ingestion

### Step 1: Get Twitter API Access
1. Sign up at https://developer.twitter.com/
2. Create a new app/project
3. Get Bearer Token (Elevated access recommended)
4. Note: Academic access provides higher limits

### Step 2: Configure Databricks Secrets
```bash
# Create secret scope
databricks secrets create-scope ai_newsletter --profile DEFAULT

# Store token
databricks secrets put-secret ai_newsletter twitter_bearer_token --profile DEFAULT
# Paste your bearer token when prompted
```

### Step 3: Update Ingestion Script
```python
# Edit src/twitter_ingestion_script.py line 22
# Change from:
bearer_token = BEARER_TOKEN_PLACEHOLDER

# To:
bearer_token = dbutils.secrets.get(scope="ai_newsletter", key="twitter_bearer_token")
```

### Step 4: Create Search Terms Table
```sql
CREATE SCHEMA IF NOT EXISTS main.config;

CREATE TABLE IF NOT EXISTS main.config.search_terms (term STRING);

INSERT INTO main.config.search_terms VALUES
  ('claude code'),
  ('databricks'),
  ('gemini'),
  ('openai'),
  ('anthropic');
```

### Step 5: Deploy and Test
```bash
# Deploy updated code
databricks bundle deploy --target default --profile DEFAULT

# Run job manually to test
databricks bundle run twitter_ingestion_job --profile DEFAULT

# Check results
databricks workspace export /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files/src/twitter_ingestion_script.py
```

### Step 6: Monitor
- Check job runs in Databricks UI: Workflows → ai_newsletter_twitter_ingestion
- Verify files appear in UC Volume every 15 minutes
- Monitor bronze table for new tweets
- Check silver table for processed data

## 📊 Expected Performance (With Real Token)

**Per 15-min Run:**
- API Call: ~1-2 seconds
- Tweets Fetched: Up to 100 (depends on query match)
- File Writes: 1-2 seconds
- Total Runtime: ~5-10 seconds

**Daily Volume:**
- Runs per day: 96 (every 15 min)
- Max tweets/day: 9,600 (if 100 per run)
- Actual tweets: Varies based on search term matches

**Bronze Processing:**
- Runs: Hourly
- Processes: All new JSON files since last run

**Silver Processing:**
- Runs: Hourly (30 min after bronze)
- Processes: New bronze records with deduplication

## 📝 Summary

**Current State:**
- ✅ Infrastructure: Complete (job, volume, tables)
- ✅ Code: Implemented and deployed
- ⚠️ Configuration: Using placeholder token
- ⚠️ Data: Using dummy tweets
- ⚠️ Features: Missing lang and author metadata

**To Go Live:**
1. Configure Twitter API token (30 min)
2. Create search terms table (5 min)
3. Test ingestion (10 min)
4. Monitor for 24 hours

**Estimated Time to Production:** 1-2 hours of configuration work

The foundation is solid - just needs configuration to start ingesting real Twitter data! 🚀
