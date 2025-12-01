# Twitter Ingestion Validation Guide

## Overview

This guide explains how to validate that Twitter ingestion is working correctly with real Twitter API data (not dummy data).

## Quick Validation

```bash
# Run validation script (2 minutes)
./tests/validation/validate_twitter_ingestion.sh

# Or comprehensive validation in Databricks
# Upload and run: tests/validation/validate_twitter_ingestion.py
```

## Validation Tests

The validation suite performs these checks:

1. **Secret Configuration** - Verifies bearer token exists in Databricks secrets
2. **Job Deployment** - Confirms Twitter ingestion job is deployed
3. **Raw Tweet Files** - Analyzes UC Volume files (dummy vs real tweets)
4. **Bronze Table** - Checks data ingestion pipeline
5. **Search Terms** - Validates search configuration

## Current Status (As of Latest Run)

### ✅ Working Components

- **Secret Scope**: `ai_newsletter_config` exists
- **Job Deployment**: Twitter ingestion job deployed successfully
- **Job Executions**: 23+ successful runs
- **File Generation**: Job is writing files to UC Volume every 15 minutes

### ❌ Issues Found

1. **All tweets are dummy data** (42 dummy files, 0 real tweets)
   - Reason: Bearer token not configured or invalid
   - Impact: No real Twitter data being ingested

2. **Bronze table not accessible**
   - Likely hasn't been created yet or needs first run

3. **Search terms table missing**
   - Using default terms: Gemini, Databricks, Claude Code, Claude, AI Driven Development

## Root Cause Analysis

The validation reveals that while the infrastructure is working perfectly:

```
Secret Scope Exists: ✅
Job Deployed:        ✅
Job Running:         ✅
Files Being Written: ✅
Real API Calls:      ❌ <- ISSUE HERE
```

The issue is on line 114 of `src/twitter_ingestion_script.py`:

```python
if bearer_token == BEARER_TOKEN_PLACEHOLDER:
    # Falls back to dummy data
    dummy_tweets = [...]
    land_tweets(dummy_tweets)
```

This confirms one of these scenarios:

### Scenario A: Secret Key Doesn't Exist

The secret scope exists, but the key `twitter_bearer_token` was never created:

```bash
# This exists
databricks secrets list-scopes --profile DEFAULT
# ai_newsletter_config  DATABRICKS

# But this might be empty or missing key
databricks secrets list --scope ai_newsletter_config --profile DEFAULT
# (no output or key not found)
```

**Solution**:
```bash
# Create the secret key with your Twitter bearer token
databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT
# Paste your bearer token when prompted
```

### Scenario B: Secret Value is Placeholder

The secret exists but contains the placeholder value:

```bash
# Secret exists but has value "YOUR_TWITTER_BEARER_TOKEN_HERE"
```

**Solution**:
```bash
# Update the secret with real token
databricks secrets delete-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT
databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT
# Paste your REAL bearer token
```

### Scenario C: Invalid/Expired Token

The token exists but is invalid or expired.

**Solution**:
1. Go to https://developer.x.com/en/portal/projects-and-apps
2. Navigate to your app → Keys and Tokens
3. Regenerate Bearer Token
4. Update Databricks secret:
   ```bash
   databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT
   ```

## Step-by-Step Fix

### Step 1: Verify Current Secret Status

Try to read the secret value (won't show the actual value for security):

```bash
# This will tell you if the key exists
databricks secrets get --scope ai_newsletter_config --key twitter_bearer_token --profile DEFAULT
# Output: "[REDACTED]" if exists, error if doesn't exist
```

### Step 2: Create or Update Secret

If the key doesn't exist or needs updating:

```bash
# Create/update the secret
databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT

# You'll be prompted to paste your token
# Paste your Twitter API v2 Bearer Token (starts with "AAAA...")
# Save and exit
```

### Step 3: Verify Token Format

A valid Twitter API v2 bearer token should:
- Be 100+ characters long
- Start with "AAAA"
- Contain alphanumeric characters
- Look like: `AAAAAAAAAAAAAAAAAAAAABcdefg...`

### Step 4: Test the Fix

```bash
# Run ingestion job manually
databricks jobs run-now 1015633920930431 --profile DEFAULT

# Wait 30 seconds, then check for real tweets
./tests/validation/validate_twitter_ingestion.sh

# You should see:
# ✅ Found X tweet files
#    - Dummy tweets: 0
#    - Real tweets:  X
```

### Step 5: Verify Real Data

Check that new files are NOT named `tweet_dummy_*`:

```bash
databricks fs ls dbfs:/Volumes/main/default/ai_newsletter_raw_tweets/ --profile DEFAULT | tail -10

# Real tweets look like:
# tweet_1234567890123456789_1764615123.json  (real tweet ID)

# Dummy tweets look like:
# tweet_dummy_1_1764614742.json  (dummy data)
```

### Step 6: Run Bronze Processing

Once real tweets are landing:

```bash
# Run bronze job to process raw files
databricks jobs list --profile DEFAULT | grep bronze
# Find the bronze job ID

databricks jobs run-now <BRONZE_JOB_ID> --profile DEFAULT

# Verify data in bronze table
databricks sql execute --statement "SELECT COUNT(*) FROM main.ai_newsletter_bronze.tweets WHERE id NOT LIKE 'dummy%'" --profile DEFAULT
```

## Expected Results After Fix

When properly configured, you should see:

```bash
==========================================
TWITTER INGESTION VALIDATION
==========================================

[TEST 1] Checking secret scope configuration...
✅ PASS: Secret scope 'ai_newsletter_config' exists

[TEST 2] Checking Twitter ingestion job...
✅ PASS: Twitter ingestion job deployed
   Job ID: 1015633920930431
   Recent successful runs: 24

[TEST 3] Checking raw tweet files in UC Volume...
✅ Found 100 tweet files
   - Dummy tweets: 42
   - Real tweets:  58

✅ PASS: Found 58 real tweets from Twitter API

   Most recent files:
   [REAL] tweet_1234567890123456789_1764615123.json
   [REAL] tweet_9876543210987654321_1764615124.json
   [REAL] tweet_5555555555555555555_1764615125.json

[TEST 4] Checking bronze table...
✅ PASS: Bronze table has 58 records
   - Dummy tweets: 0
   - Real tweets:  58

✅ Bronze table contains 58 real tweets

[TEST 5] Checking search terms configuration...
⚠️  WARNING: Search terms table does not exist
   Using default terms

==========================================
VALIDATION SUMMARY
==========================================
Total Tests: 5
Passed:   4
Failed:   0
Warnings: 1

🎉 TWITTER INGESTION VALIDATED!

✅ Twitter API integration working
✅ Real tweets being ingested
✅ Bronze pipeline processing data
```

## Monitoring Real-Time Ingestion

### Check Job Logs

1. Go to Databricks Workspace
2. Navigate to Workflows → ai_newsletter_twitter_ingestion
3. Click on latest run
4. Check output logs for:

```
Fetching tweets with query: Gemini OR Databricks OR Claude Code OR Claude OR AI Driven Development lang:en -is:retweet
Fetched 87 tweets.
Landed tweet 1234567890123456789 to /Volumes/main/default/ai_newsletter_raw_tweets/tweet_1234567890123456789_1764615123.json
Landed tweet 9876543210987654321 to /Volumes/main/default/ai_newsletter_raw_tweets/tweet_9876543210987654321_1764615124.json
...
```

If you see this instead, token is NOT configured:
```
WARNING: Bearer token is a placeholder. Please configure Databricks secrets.
Simulating tweet fetching and landing with dummy data.
Landed tweet dummy_1 to /Volumes/main/default/ai_newsletter_raw_tweets/tweet_dummy_1_1764615123.json
```

### Check Volume Files Real-Time

```bash
# Watch for new files (run in loop)
while true; do
    echo "=== $(date) ==="
    databricks fs ls dbfs:/Volumes/main/default/ai_newsletter_raw_tweets/ --profile DEFAULT | \
        grep "tweet_" | \
        tail -5 | \
        awk '{print $NF}'
    echo ""
    sleep 60
done
```

### Check API Rate Limits

```bash
# Test Twitter API directly
curl -X GET "https://api.twitter.com/2/tweets/search/recent?query=databricks&max_results=10" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "User-Agent: DatabricksAISignalApp"

# Look for rate limit headers in response:
# x-rate-limit-limit: 450
# x-rate-limit-remaining: 449
# x-rate-limit-reset: 1764615600
```

## Troubleshooting

### Issue: Validation still shows dummy tweets after configuring secret

**Diagnosis**:
```bash
# Check if job picked up the secret
databricks jobs list-runs --limit 1 --profile DEFAULT | grep twitter

# Check if there are newer files
databricks fs ls dbfs:/Volumes/main/default/ai_newsletter_raw_tweets/ --profile DEFAULT | \
    tail -10 | \
    awk '{print $NF}'
```

**Solution**:
- Redeploy bundle: `databricks bundle deploy --target default --profile DEFAULT`
- Run job manually: `databricks jobs run-now 1015633920930431 --profile DEFAULT`
- Check job logs for errors

### Issue: API returns 401 Unauthorized

**Cause**: Invalid or expired bearer token

**Solution**:
1. Regenerate token at developer.x.com
2. Update secret
3. Rerun job

### Issue: API returns 429 Rate Limit

**Cause**: Exceeded Twitter API rate limits

**Solution**:
- Free tier: 10K tweets/month = ~330 tweets/day
- Your schedule: 96 runs/day × 100 tweets = 9,600 tweets/day
- **Reduce frequency** or **upgrade to Basic tier ($100/month)**

```yaml
# Change schedule in databricks.yml to hourly:
schedule:
  quartz_cron_expression: "0 0 * * * ?"  # Every hour (2,400 tweets/day)
```

### Issue: No tweets matching search terms

**Cause**: Search terms too specific or no recent activity

**Solution**:
```sql
-- Add more search terms
CREATE TABLE IF NOT EXISTS main.config.search_terms (term STRING);

INSERT INTO main.config.search_terms VALUES
  ('AI'),
  ('artificial intelligence'),
  ('machine learning'),
  ('deep learning'),
  ('LLM'),
  ('ChatGPT'),
  ('Claude'),
  ('Gemini'),
  ('Databricks');
```

## Next Steps After Validation Passes

Once you see real tweets being ingested:

1. ✅ **Monitor for 24 hours** - Ensure continuous ingestion
2. ✅ **Run bronze processing** - Process raw tweets into bronze table
3. ✅ **Verify silver table** - Run T007 validation for influence scoring
4. ✅ **Check data quality** - Review tweet content and metrics
5. ✅ **Optimize search terms** - Refine based on relevance
6. ⏭️ **Proceed to T008** - Implement gold daily materialized view

## Validation Files

- `tests/validation/validate_twitter_ingestion.sh` - CLI validation (2 min)
- `tests/validation/validate_twitter_ingestion.py` - Databricks notebook (5 min)
- `tests/validation/TWITTER_INGESTION_VALIDATION.md` - This guide

## Quick Reference Commands

```bash
# Create/update secret
databricks secrets put-secret ai_newsletter_config twitter_bearer_token --profile DEFAULT

# Run validation
./tests/validation/validate_twitter_ingestion.sh

# Deploy and run
databricks bundle deploy --target default --profile DEFAULT
databricks jobs run-now 1015633920930431 --profile DEFAULT

# Check files
databricks fs ls dbfs:/Volumes/main/default/ai_newsletter_raw_tweets/ --profile DEFAULT | tail -10

# Check bronze table
databricks sql execute --statement "SELECT COUNT(*) FROM main.ai_newsletter_bronze.tweets" --profile DEFAULT

# View job logs
# Go to Databricks UI: Workflows → ai_newsletter_twitter_ingestion → Latest Run
```

## Support

If validation continues to fail:

1. Check job logs in Databricks UI
2. Review `TWITTER_INGESTION_STATUS.md` for detailed implementation notes
3. Test Twitter API directly with curl
4. Verify token at developer.x.com/en/portal/projects-and-apps
