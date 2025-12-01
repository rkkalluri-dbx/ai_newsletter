# Gold Layer Validation Guide (T008 & T009)

This guide explains how to validate the gold layer implementation for the AI Signal Newsletter project.

## Overview

The gold layer consists of three tables:
- **`main.ai_newsletter_gold.daily_top_candidates`** (T008): Top 100 tweets per day by influence score
- **`main.ai_newsletter_gold.weekly_top_stories`** (T009): Top 200 tweets from last 7 days
- **`main.ai_newsletter_gold.weekly_trending_authors`** (T009): Top 20 trending authors

## Validation Tools

We provide two complementary validation tools:

### 1. CLI Validation Script
**File**: `tests/validation/validate_gold_layer.sh`

Quick validation that can be run from your terminal without accessing Databricks UI.

**What it validates**:
- ✅ Gold daily job deployment
- ✅ Gold weekly job deployment
- ✅ Job schedules (daily at 06:00 and 07:00 UTC)
- ✅ Source files exist (gold_daily_view.py, gold_weekly_rollup.py)
- ✅ Scripts deployed to Databricks workspace
- ✅ Implementation features (top 100, influence_score, partitioning, etc.)

**How to run**:
```bash
cd /Users/rkalluri/projects/ai_newsletter
./tests/validation/validate_gold_layer.sh
```

**Expected output**:
```
==========================================
GOLD LAYER VALIDATION (T008 & T009)
==========================================

Tables to validate:
  - main.ai_newsletter_gold.daily_top_candidates
  - main.ai_newsletter_gold.weekly_top_stories
  - main.ai_newsletter_gold.weekly_trending_authors

[TEST 1] Checking gold daily job deployment...
✅ PASS: Gold daily job deployed
   Job ID: <JOB_ID>
   Recent successful runs: X

[TEST 2] Checking gold weekly job deployment...
✅ PASS: Gold weekly job deployed
   Job ID: <JOB_ID>
   Recent successful runs: X

...

==========================================
VALIDATION SUMMARY
==========================================
Total Tests: 9
Passed:   9
Failed:   0
Warnings: 0

🎉 ALL TESTS PASSED!
```

### 2. Databricks Validation Notebook
**File**: `tests/validation/validate_gold_layer.py`

Comprehensive validation that performs detailed SQL queries and data quality checks.

**What it validates**:
- ✅ Table existence (all 3 gold tables)
- ✅ Schema correctness (all required columns present)
- ✅ Row counts (100 for daily, 200 for weekly, 20 for authors)
- ✅ Ranking logic (sequential ranks, proper ordering by influence_score)
- ✅ Partitioning strategy (by tweet_date and week_start_date)
- ✅ Data quality (no nulls, valid score ranges)
- ✅ Weekly aggregations (date ranges, author metrics)
- ✅ Relationship with silver table (proper subsets)

**How to run**:

1. Upload to Databricks workspace:
   ```bash
   databricks workspace import tests/validation/validate_gold_layer.py \
     /Workspace/Users/rkalluri@gmail.com/tests/validate_gold_layer \
     --language PYTHON --overwrite --profile DEFAULT
   ```

2. Open in Databricks UI:
   - Navigate to Workspace → Users → rkalluri@gmail.com → tests
   - Click on `validate_gold_layer` notebook
   - Click "Run All" to execute all validation tests

3. Review results in the notebook output

**Expected output**:
```
==========================================
GOLD LAYER VALIDATION
==========================================
Silver Table: main.ai_newsletter_silver.tweets
Daily Table: main.ai_newsletter_gold.daily_top_candidates
Weekly Table: main.ai_newsletter_gold.weekly_top_stories
Authors Table: main.ai_newsletter_gold.weekly_trending_authors
==========================================

[TEST 1] Checking table existence...
✅ PASS: Daily table exists - main.ai_newsletter_gold.daily_top_candidates
✅ PASS: Weekly table exists - main.ai_newsletter_gold.weekly_top_stories
✅ PASS: Trending authors table exists - main.ai_newsletter_gold.weekly_trending_authors

[TEST 2] Validating table schemas...
✅ PASS: Daily table has all required columns (14 columns)
✅ PASS: Weekly table has all required columns (15 columns)

...

==========================================
VALIDATION SUMMARY
==========================================
Total Tests: 20
Passed:   20
Failed:   0
Warnings: 0

🎉 ALL TESTS PASSED!
```

## What Each Test Does

### CLI Script Tests

| Test | What It Checks | Pass Criteria |
|------|----------------|---------------|
| 1 | Gold daily job deployment | Job `ai_newsletter_gold_daily_view` exists |
| 2 | Gold weekly job deployment | Job `ai_newsletter_gold_weekly_rollup` exists |
| 3 | Daily table script | `src/gold_daily_view.py` deployed to workspace |
| 4 | Weekly table script | `src/gold_weekly_rollup.py` deployed to workspace |
| 5 | Job schedules | Daily at 06:00 UTC, weekly at 07:00 UTC |
| 6 | Source files | Both .py files exist locally |
| 7 | Implementation features | Code contains required patterns (top 100, influence_score, etc.) |

### Notebook Tests

| Test | What It Checks | Pass Criteria |
|------|----------------|---------------|
| 1 | Table existence | All 3 tables can be read |
| 2 | Schema validation | All required columns present |
| 3 | Row count validation | Daily ≤ 100, Weekly ≤ 200, Authors ≤ 20 |
| 4 | Ranking logic | Sequential ranks, descending influence_score |
| 5 | Partitioning | Proper partitioning by date columns |
| 6 | Data quality | No nulls in critical columns, valid score ranges |
| 7 | Weekly aggregations | Correct date ranges, author metrics |
| 8 | Silver comparison | Gold tables are proper subsets of silver |

## Troubleshooting

### Common Issues

#### Issue 1: Jobs Not Found
**Symptom**: `❌ FAIL: Gold daily/weekly job not found`

**Solution**:
```bash
# Deploy the bundle
databricks bundle deploy --target default --profile DEFAULT

# Verify deployment
databricks jobs list --profile DEFAULT | grep "gold"
```

#### Issue 2: Empty Tables
**Symptom**: `⚠️ WARNING: Table is empty`

**Solution**:
Run the pipeline in sequence:
```bash
# 1. Run twitter ingestion (should already be running every 15 min)
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "twitter_ingestion" | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID --profile DEFAULT

# Wait a few minutes, then:

# 2. Run bronze processing
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "bronze_processing" | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID --profile DEFAULT

# 3. Run silver processing
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "silver_processing" | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID --profile DEFAULT

# 4. Run gold daily view
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "gold_daily" | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID --profile DEFAULT

# 5. Run gold weekly rollup
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "gold_weekly" | awk '{print $1}')
databricks jobs run-now --job-id $JOB_ID --profile DEFAULT
```

#### Issue 3: Job Failures
**Symptom**: Jobs exist but have no successful runs or recent failures

**Solution**:
```bash
# Get job ID
JOB_ID=$(databricks jobs list --profile DEFAULT | grep "gold_daily" | awk '{print $1}')

# Check recent runs
databricks jobs list-runs --job-id $JOB_ID --limit 5 --profile DEFAULT

# View logs in Databricks UI:
# Workflows → ai_newsletter_gold_daily_view → Click on failed run → View logs
```

Common failure reasons:
- **Silver table empty**: Wait for upstream jobs to complete first
- **Permission issues**: Check Unity Catalog permissions on silver tables
- **Compute issues**: Check cluster configuration in databricks.yml

#### Issue 4: Incorrect Rankings
**Symptom**: `❌ FAIL: Tweets not properly ordered by influence_score`

**Solution**:
This indicates a logic error in the ranking window function. Check:
```python
# In gold_daily_view.py, ensure:
window_spec = Window.partitionBy("tweet_date").orderBy(col("influence_score").desc())

# In gold_weekly_rollup.py, ensure:
window_spec = Window.orderBy(col("influence_score").desc())
```

#### Issue 5: Missing Source Files
**Symptom**: `❌ FAIL: src/gold_daily_view.py not found`

**Solution**:
```bash
# Check if files exist locally
ls -la src/gold_*.py

# If missing, they may not have been committed. Check git status:
git status

# If uncommitted, commit them:
git add src/gold_daily_view.py src/gold_weekly_rollup.py
git commit -m "Add gold layer implementation"
git push
```

## Pipeline Status Check

To get a complete picture of the pipeline status:

```bash
# Check all jobs
databricks jobs list --profile DEFAULT | grep "ai_newsletter"

# Check recent runs for all jobs
for job in "twitter_ingestion" "bronze_processing" "silver_processing" "gold_daily" "gold_weekly"; do
  echo "=== $job ==="
  JOB_ID=$(databricks jobs list --profile DEFAULT | grep "$job" | awk '{print $1}')
  if [ -n "$JOB_ID" ]; then
    databricks jobs list-runs --job-id $JOB_ID --limit 3 --profile DEFAULT
  fi
  echo
done
```

## Expected Data Flow

```
Twitter API (every 15 min)
    ↓
    → Raw JSON files in UC Volume
    ↓
Bronze Processing (hourly at :00)
    → main.ai_newsletter_bronze.tweets
    ↓
Silver Processing (hourly at :30)
    → main.ai_newsletter_silver.tweets (with influence_score)
    ↓
Gold Daily View (daily at 06:00 UTC) ← T008
    → main.ai_newsletter_gold.daily_top_candidates (top 100)
    ↓
Gold Weekly Rollup (daily at 07:00 UTC) ← T009
    → main.ai_newsletter_gold.weekly_top_stories (top 200, last 7 days)
    → main.ai_newsletter_gold.weekly_trending_authors (top 20 authors)
```

## Validation Frequency

### During Development
Run validation after:
- ✅ Every code change to gold layer scripts
- ✅ After redeploying the bundle
- ✅ After running jobs manually

### In Production
Run validation:
- ✅ Daily (automated via CI/CD)
- ✅ After any pipeline failures
- ✅ Before starting work on Epic 3 (LLM agent)

## Success Criteria

The gold layer is considered validated when:
- ✅ CLI validation shows 9/9 tests passed (or only warnings)
- ✅ Databricks notebook validation shows 20/20 tests passed (or only warnings)
- ✅ Both jobs have at least one successful run
- ✅ Daily table contains ≤100 records per day
- ✅ Weekly table contains ≤200 records
- ✅ All rankings are sequential and properly ordered
- ✅ No null values in critical columns
- ✅ Tables are properly partitioned

## Next Steps

Once validation passes:
1. ✅ Mark T008 and T009 as complete in specs/tasks.md
2. ✅ Close GitHub issues #2 and #3
3. ✅ Commit and push validation scripts
4. ✅ Create PR to merge epic-3-llm-processing branch
5. ➡️ Start Epic 3: LLM Summarization Agent (T010-T012)

## Resources

- Gold daily view script: `src/gold_daily_view.py`
- Gold weekly rollup script: `src/gold_weekly_rollup.py`
- Job configuration: `databricks.yml` (lines 63-85)
- GitHub issues: #2 (T008), #3 (T009)
- Databricks UI: https://dbc-2647a0d2-b28d.cloud.databricks.com
- Project plan: `specs/tasks.md`
