# T007 Validation Guide: Silver Table Implementation

This guide provides multiple methods to validate the T007 implementation (Silver table with deduplication, enrichment, and influence scoring).

## Quick Validation (5 minutes)

### Option 1: Run the Automated Validation Script

```bash
# Upload and run the validation notebook in Databricks
databricks workspace import validate_t007.py \
  /Workspace/Users/rkalluri@gmail.com/validate_t007 \
  --language PYTHON \
  --profile DEFAULT

# Or run it as a one-time job
databricks bundle run ai_newsletter_silver_job --profile DEFAULT
```

### Option 2: Manual SQL Validation

Connect to your Databricks workspace and run these SQL queries:

```sql
-- 1. Check if silver table exists and has data
SELECT COUNT(*) as total_records
FROM main.ai_newsletter_silver.tweets;

-- 2. Verify deduplication (should return 0 duplicates)
SELECT
  COUNT(*) - COUNT(DISTINCT tweet_id) as duplicate_count
FROM main.ai_newsletter_silver.tweets;

-- 3. Check influence score statistics
SELECT
  COUNT(*) as total,
  AVG(influence_score) as avg_score,
  MIN(influence_score) as min_score,
  MAX(influence_score) as max_score,
  PERCENTILE(influence_score, 0.5) as median_score
FROM main.ai_newsletter_silver.tweets;

-- 4. Verify schema
DESCRIBE main.ai_newsletter_silver.tweets;

-- 5. Show top tweets by influence score
SELECT
  tweet_id,
  SUBSTRING(text, 1, 50) as text_preview,
  like_count,
  retweet_count,
  reply_count,
  influence_score
FROM main.ai_newsletter_silver.tweets
ORDER BY influence_score DESC
LIMIT 10;
```

## Comprehensive Validation (15 minutes)

### Step 1: Prerequisites Check

Before validating the silver table, ensure prerequisites are met:

```bash
# 1. Check bronze table has data
databricks sql execute \
  --statement "SELECT COUNT(*) FROM main.ai_newsletter_bronze.tweets" \
  --profile DEFAULT

# 2. Verify silver job is deployed
databricks bundle validate --target default --profile DEFAULT
```

### Step 2: Run Silver Processing Job

```bash
# Trigger the silver processing job manually
databricks bundle run ai_newsletter_silver_job --profile DEFAULT

# Monitor the job status in Databricks UI:
# Workflows → ai_newsletter_silver_processing → View Latest Run
```

### Step 3: Data Quality Validation

Run these SQL queries to validate data quality:

#### A. Deduplication Validation

```sql
-- Check for duplicate tweet_ids (should return empty result)
SELECT tweet_id, COUNT(*) as count
FROM main.ai_newsletter_silver.tweets
GROUP BY tweet_id
HAVING COUNT(*) > 1;

-- Compare bronze vs silver record counts
SELECT
  (SELECT COUNT(DISTINCT id) FROM main.ai_newsletter_bronze.tweets) as bronze_unique,
  (SELECT COUNT(DISTINCT tweet_id) FROM main.ai_newsletter_silver.tweets) as silver_unique,
  (SELECT COUNT(*) FROM main.ai_newsletter_silver.tweets) as silver_total;
```

#### B. Influence Score Validation

```sql
-- Check for null or invalid influence scores
SELECT
  SUM(CASE WHEN influence_score IS NULL THEN 1 ELSE 0 END) as null_scores,
  SUM(CASE WHEN influence_score < 0 THEN 1 ELSE 0 END) as negative_scores,
  SUM(CASE WHEN influence_score = 0 THEN 1 ELSE 0 END) as zero_scores
FROM main.ai_newsletter_silver.tweets;

-- Manually verify influence score calculation for a sample
SELECT
  tweet_id,
  like_count,
  retweet_count,
  reply_count,
  follower_count,
  influence_score,
  -- Manual calculation: (likes * 2) + (retweets * 3) + (replies * 1) + (followers / 1000)
  (like_count * 2) + (retweet_count * 3) + (reply_count * 1) + (follower_count / 1000.0) as expected_score,
  ABS(influence_score - ((like_count * 2) + (retweet_count * 3) + (reply_count * 1) + (follower_count / 1000.0))) as difference
FROM main.ai_newsletter_silver.tweets
LIMIT 10;
```

#### C. Schema Validation

```sql
-- Verify all expected columns exist with correct types
SELECT column_name, data_type
FROM main.information_schema.columns
WHERE table_schema = 'ai_newsletter_silver'
  AND table_name = 'tweets'
ORDER BY ordinal_position;

-- Expected columns:
-- tweet_id (STRING)
-- text (STRING)
-- author_id (STRING)
-- author_name (STRING)
-- follower_count (BIGINT)
-- verified (BOOLEAN)
-- created_at (TIMESTAMP)
-- like_count (BIGINT)
-- retweet_count (BIGINT)
-- reply_count (BIGINT)
-- influence_score (DOUBLE)
-- processed_at (TIMESTAMP)
```

#### D. Data Completeness Check

```sql
-- Check for null values in critical fields
SELECT
  COUNT(*) as total_records,
  SUM(CASE WHEN tweet_id IS NULL THEN 1 ELSE 0 END) as null_tweet_id,
  SUM(CASE WHEN text IS NULL THEN 1 ELSE 0 END) as null_text,
  SUM(CASE WHEN author_id IS NULL THEN 1 ELSE 0 END) as null_author_id,
  SUM(CASE WHEN influence_score IS NULL THEN 1 ELSE 0 END) as null_influence_score,
  SUM(CASE WHEN processed_at IS NULL THEN 1 ELSE 0 END) as null_processed_at
FROM main.ai_newsletter_silver.tweets;
```

### Step 4: Functional Testing

#### Test Scenario 1: Deduplication

```sql
-- Create test data with duplicates in bronze table (if needed for testing)
-- Then run silver processing and verify only one record per tweet_id remains

-- Check if deduplication is working
WITH tweet_counts AS (
  SELECT
    tweet_id,
    COUNT(*) as occurrence_count,
    MAX(processed_at) as latest_processing
  FROM main.ai_newsletter_silver.tweets
  GROUP BY tweet_id
)
SELECT
  MAX(occurrence_count) as max_occurrences,
  SUM(CASE WHEN occurrence_count > 1 THEN 1 ELSE 0 END) as tweets_with_duplicates
FROM tweet_counts;
-- Expected: max_occurrences = 1, tweets_with_duplicates = 0
```

#### Test Scenario 2: Influence Score Ranking

```sql
-- Verify tweets are properly ranked by influence score
SELECT
  ROW_NUMBER() OVER (ORDER BY influence_score DESC) as rank,
  tweet_id,
  SUBSTRING(text, 1, 100) as text_preview,
  like_count,
  retweet_count,
  reply_count,
  follower_count,
  influence_score
FROM main.ai_newsletter_silver.tweets
ORDER BY influence_score DESC
LIMIT 20;
```

#### Test Scenario 3: Data Freshness

```sql
-- Check when data was last processed
SELECT
  MAX(processed_at) as last_processed,
  MIN(processed_at) as first_processed,
  COUNT(*) as total_records,
  COUNT(DISTINCT DATE(processed_at)) as processing_days
FROM main.ai_newsletter_silver.tweets;
```

### Step 5: Performance Validation

```sql
-- Check table size and partitioning
DESCRIBE DETAIL main.ai_newsletter_silver.tweets;

-- Check query performance
SELECT COUNT(*) FROM main.ai_newsletter_silver.tweets
WHERE influence_score > 100;

-- Check for data skew
SELECT
  DATE(created_at) as date,
  COUNT(*) as tweet_count,
  AVG(influence_score) as avg_score
FROM main.ai_newsletter_silver.tweets
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;
```

## Validation Checklist

Use this checklist to confirm T007 implementation:

### Core Requirements
- [ ] Silver table `main.ai_newsletter_silver.tweets` exists
- [ ] Table has records (> 0)
- [ ] Schema matches specification (12 columns)
- [ ] All column types are correct

### Deduplication
- [ ] No duplicate tweet_ids exist
- [ ] Deduplication query returns 0 duplicates
- [ ] Silver unique count ≤ Bronze unique count

### Influence Score
- [ ] No null influence scores
- [ ] No negative influence scores
- [ ] Manual calculation matches UDF calculation
- [ ] Score distribution looks reasonable (avg > 0)

### Data Quality
- [ ] No null tweet_ids
- [ ] No null text fields
- [ ] All records have processed_at timestamp
- [ ] processed_at is recent (within expected time frame)

### Job Configuration
- [ ] Job `ai_newsletter_silver_job` exists in Databricks
- [ ] Job schedule is configured (hourly at :30)
- [ ] Job runs successfully without errors
- [ ] Job completes in reasonable time (< 10 minutes)

### Integration
- [ ] Bronze table has source data
- [ ] Silver job runs after bronze job
- [ ] Data flows correctly from bronze to silver
- [ ] No data loss during transformation

## Expected Results

### Successful Validation Output

When validation is successful, you should see:

```
✅ Bronze table has X records
✅ Silver table exists with Y records
✅ All expected columns present: 12 columns
✅ PASS: Perfect deduplication (0 duplicates)
✅ PASS: No null or negative influence scores
✅ PASS: Silver has same or fewer records
✅ PASS: All records have processed_at timestamp
✅ Passed: 9/9 tests

🎉 ALL TESTS PASSED! T007 implementation is validated.
```

### Common Issues and Solutions

#### Issue 1: Silver table is empty
**Cause:** Bronze table has no data or job hasn't run
**Solution:**
```bash
# Run bronze job first
databricks bundle run ai_newsletter_bronze_job --profile DEFAULT

# Then run silver job
databricks bundle run ai_newsletter_silver_job --profile DEFAULT
```

#### Issue 2: Duplicates found
**Cause:** Deduplication logic not working
**Solution:** Check the window function in silver_processing.py line ~80

#### Issue 3: Null influence scores
**Cause:** UDF failing or null input values
**Solution:** Check for null values in like_count, retweet_count, reply_count

#### Issue 4: Job fails with permission error
**Cause:** Insufficient permissions on schema or volume
**Solution:** Grant permissions:
```sql
GRANT ALL PRIVILEGES ON SCHEMA main.ai_newsletter_silver TO `rkalluri@gmail.com`;
```

## Automated Validation

For CI/CD pipelines, use the validation script:

```bash
# Run validation as part of deployment
databricks workspace import validate_t007.py \
  /Workspace/Users/rkalluri@gmail.com/validate_t007 \
  --profile DEFAULT

# Execute validation
databricks workspace run /Workspace/Users/rkalluri@gmail.com/validate_t007 \
  --profile DEFAULT
```

## Next Steps After Validation

Once T007 is validated:

1. **Monitor in Production**
   - Check Databricks SQL dashboard
   - Monitor job execution times
   - Track influence score distribution

2. **Optimize if Needed**
   - Add partitioning by date if table grows large
   - Optimize deduplication window function
   - Tune influence score formula based on data

3. **Proceed to T008**
   - Gold daily materialized view
   - Top 100 candidates per day

4. **Close GitHub Issue**
   ```bash
   gh issue close 1 --comment "T007 validated and deployed successfully"
   ```

## Support

If validation fails:
1. Check Databricks job logs in Workflows UI
2. Review error messages in validation output
3. Verify bronze table has data
4. Check Unity Catalog permissions
5. Refer to TROUBLESHOOTING.md (if available)
