# Epic 2: Data Pipeline (Bronze → Silver → Gold)

**Branch:** `epic-2-data-pipeline`
**Status:** In Progress
**Started:** December 2025

## Overview

Build the data transformation pipeline that processes raw tweets from the bronze layer through deduplication, enrichment, and aggregation to create silver and gold tables optimized for LLM agent consumption.

## Tasks

### T007: Silver Table with Deduplication & Enrichment
**Status:** 🔲 Not Started

**Objective:** Create a silver Delta table that deduplicates tweets, filters for English language, enriches with author metadata, and calculates an influence score.

**Requirements:**
- Deduplicate tweets by tweet ID
- Filter for `lang=en`
- Enrich with author metadata (followers, verification status)
- Calculate `influence_score` using a UDF
  - Formula: `(likes * 2) + (retweets * 3) + (replies * 1) + (follower_count / 1000)`
- Schema:
  ```
  tweet_id: string
  text: string
  author_id: string
  author_name: string
  follower_count: long
  verified: boolean
  created_at: timestamp
  like_count: long
  retweet_count: long
  reply_count: long
  influence_score: double
  processed_at: timestamp
  ```

**Deliverables:**
- `src/silver_processing.py` - Silver table processing job
- Update `databricks.yml` to add silver job
- Table: `ai_newsletter_silver.tweets`

---

### T008: Gold Daily Materialized View
**Status:** 🔲 Not Started

**Objective:** Create a daily materialized view that selects the top 100 tweet candidates per day, ranked by influence score.

**Requirements:**
- Materialized view refreshed daily at 06:00 UTC
- Select top 100 tweets per day based on `influence_score`
- Include all silver table columns plus ranking
- Partition by date for efficient querying
- Schema extends silver with:
  ```
  daily_rank: integer
  story_date: date
  ```

**Deliverables:**
- `src/gold_daily_view.py` - Daily materialized view creation
- Update `databricks.yml` to add daily refresh job
- View: `ai_newsletter_gold.daily_top_candidates`

---

### T009: Gold Weekly Rollup View
**Status:** 🔲 Not Started

**Objective:** Create a weekly rollup view that aggregates the last 7 days of top stories for the weekly newsletter edition.

**Requirements:**
- Rolling 7-day window (last 7 days from current date)
- Aggregate top stories by topic/theme
- Calculate weekly engagement metrics
- Include trending authors
- Schema:
  ```
  week_start_date: date
  week_end_date: date
  tweet_id: string
  text: string
  author_name: string
  total_engagement: long (sum of all metrics)
  weekly_rank: integer
  topic_category: string (optional, for future ML classification)
  ```

**Deliverables:**
- `src/gold_weekly_rollup.py` - Weekly rollup view
- Update `databricks.yml` to add weekly job
- View: `ai_newsletter_gold.weekly_top_stories`

---

## Implementation Order

1. **Start with T007** - Silver table is foundation for all downstream processing
2. **Then T008** - Daily view needed for LLM agent (Epic 3)
3. **Finally T009** - Weekly rollup for weekly edition

## Architecture

```
Bronze (ai_newsletter_bronze.tweets)
    ↓
Silver (ai_newsletter_silver.tweets)
    ├── Deduplication by tweet_id
    ├── Language filter (lang=en)
    ├── Author enrichment
    └── Influence score calculation
    ↓
Gold Daily (ai_newsletter_gold.daily_top_candidates)
    └── Top 100 per day by influence_score
    ↓
Gold Weekly (ai_newsletter_gold.weekly_top_stories)
    └── 7-day rollup for weekly newsletter
```

## Development Workflow

```bash
# Working on Epic 2 branch
git checkout epic-2-data-pipeline

# Create/edit transformation scripts
code src/silver_processing.py

# Validate and deploy
databricks bundle validate --target default --profile DEFAULT
databricks bundle deploy --target default --profile DEFAULT

# Test the job
databricks bundle run silver_processing_job --profile DEFAULT

# Commit progress
git add src/silver_processing.py databricks.yml
git commit -m "Implement T007: Silver table with deduplication"
git push
```

## Testing Strategy

1. **Unit Testing:**
   - Test influence_score UDF with sample data
   - Verify deduplication logic
   - Test language filtering

2. **Integration Testing:**
   - Run full bronze → silver pipeline with test data
   - Verify silver table schema and data quality
   - Check materialized view refresh schedules

3. **Data Quality Checks:**
   - No duplicate tweet IDs in silver table
   - All tweets are lang=en
   - influence_score > 0 for all records
   - Daily view contains exactly top 100 per day

## Success Criteria

- [ ] Silver table successfully deduplicates and enriches bronze data
- [ ] Daily gold view contains top 100 candidates per day
- [ ] Weekly rollup provides 7-day aggregation
- [ ] All jobs run on schedule without errors
- [ ] Data quality checks pass
- [ ] Pipeline handles incremental updates efficiently

## Timeline Estimate

- T007: 2-3 days (silver table + influence scoring)
- T008: 1-2 days (daily materialized view)
- T009: 1-2 days (weekly rollup)
- **Total: 4-7 days**

## Dependencies

**Completed:**
- ✅ Epic 1: Bronze layer ingestion

**Blocked By:** None

**Blocks:**
- Epic 3: LLM Summarization Agent (needs daily gold view)

## Notes

- Consider adding data quality monitoring
- May need to adjust influence_score formula based on real data
- Future: Add ML-based topic classification for better categorization
