# Configuration Data Seeding Guide

This guide explains how to seed and manage the configuration data for the AI Newsletter pipeline.

## Overview

The `main.config.search_terms` table stores search terms used by the Twitter ingestion job. This table must be seeded before running the pipeline.

## Table Schema

```sql
CREATE TABLE main.config.search_terms (
  term STRING NOT NULL,              -- Search term (e.g., "Claude", "Databricks")
  active BOOLEAN,                     -- Whether to use this term in searches
  category STRING,                    -- Category for organization (e.g., "AI", "Tool")
  description STRING,                 -- What this term tracks
  created_at TIMESTAMP,               -- When term was added
  updated_at TIMESTAMP                -- Last modification time
)
```

## Default Search Terms

The seeding script includes these default terms:

| Term | Category | Description |
|------|----------|-------------|
| Gemini | AI | Google's Gemini AI model |
| Databricks | Database | Databricks data lakehouse platform |
| Claude Code | Tool | Anthropic's Claude Code tool |
| Claude | AI | Anthropic's Claude AI assistant |
| AI Driven Development | Trend | AI-assisted development |
| GPT-4 | AI | OpenAI's GPT-4 model |
| ChatGPT | Tool | OpenAI's ChatGPT |
| LLM | AI | Large Language Models |
| Machine Learning | AI | General ML discussions |
| Delta Lake | Database | Delta Lake storage layer |

## How to Seed Configuration

### Method 1: Upload and Run in Databricks UI (Recommended)

**Step 1: Upload the notebook**
```bash
# From project root directory
./scripts/seed_config.sh
```

**Step 2: Run in Databricks**
1. Open Databricks UI: https://dbc-2647a0d2-b28d.cloud.databricks.com
2. Navigate to: Workspace → Users → rkalluri@gmail.com → `seed_config`
3. Attach a cluster
4. Click **"Run All"**

**Expected Output:**
```
==========================================
CONFIGURATION DATA SEEDING
==========================================
Target Table: main.config.search_terms
==========================================

[STEP 1] Creating config schema...
✅ Schema created/verified: main.config

[STEP 2] Creating search_terms table...
✅ Table created: main.config.search_terms

[STEP 3] Defining seed data...
Defined 10 search terms to seed

[STEP 4] Seeding search terms...
Current records in table: 0
✅ Seeding complete!
   Total records: 10
   New records: 10
   Updated records: 0

[STEP 5] Verifying seeded data...
All search terms displayed...

[STEP 6] Testing query string generation...
✅ Query string is within Twitter API limit

==========================================
SEEDING COMPLETE
==========================================
✅ Configuration table seeded
   Total search terms: 10
   Active terms: 10
   Inactive terms: 0
```

### Method 2: Direct SQL (Quick Add)

To add a single term directly:

```sql
INSERT INTO main.config.search_terms
VALUES (
  'Anthropic',                           -- term
  true,                                  -- active
  'AI',                                  -- category
  'Anthropic AI company news',           -- description
  current_timestamp(),                   -- created_at
  current_timestamp()                    -- updated_at
);
```

## Managing Search Terms

### View All Terms

```sql
SELECT * FROM main.config.search_terms
ORDER BY category, term;
```

### View Active Terms Only

```sql
SELECT term, category, description
FROM main.config.search_terms
WHERE active = true
ORDER BY category;
```

### Add New Term

```sql
INSERT INTO main.config.search_terms
VALUES ('OpenAI', true, 'AI', 'OpenAI company and products', current_timestamp(), current_timestamp());
```

### Deactivate a Term (Don't Delete)

```sql
UPDATE main.config.search_terms
SET active = false, updated_at = current_timestamp()
WHERE term = 'term_to_deactivate';
```

### Reactivate a Term

```sql
UPDATE main.config.search_terms
SET active = true, updated_at = current_timestamp()
WHERE term = 'term_to_reactivate';
```

### Update Term Details

```sql
UPDATE main.config.search_terms
SET
  category = 'new_category',
  description = 'updated description',
  updated_at = current_timestamp()
WHERE term = 'term_name';
```

### Delete a Term (Permanent)

```sql
DELETE FROM main.config.search_terms
WHERE term = 'term_to_delete';
```

## Adding Custom Terms

To add your own search terms, edit `src/seed_config.py`:

```python
seed_terms = [
    # ... existing terms ...
    {
        "term": "Your Custom Term",
        "active": True,
        "category": "Custom",
        "description": "Description of what this tracks"
    }
]
```

Then re-run the seeding script. It's safe to run multiple times (idempotent).

## Twitter Query String

The active search terms are combined into a Twitter API query:

```python
query_string = " OR ".join(active_terms) + " lang:en -is:retweet"
```

**Example:**
```
Gemini OR Databricks OR "Claude Code" OR Claude OR ... lang:en -is:retweet
```

### Query String Limits

- **Twitter API limit**: 512 characters
- The seeding script checks this and warns if exceeded
- If too long, either:
  1. Deactivate less important terms
  2. Use shorter term variations
  3. Split into multiple ingestion jobs

### Check Current Query String

```sql
-- Get active terms
SELECT term FROM main.config.search_terms WHERE active = true;

-- Count characters (approximate)
SELECT SUM(LENGTH(term) + 4) as approx_length  -- +4 for " OR "
FROM main.config.search_terms
WHERE active = true;
```

## Integration with Pipeline

### How It's Used

1. **Twitter Ingestion Job** (`src/twitter_ingestion_script.py`):
   ```python
   search_terms_df = spark.read.format("delta").table("main.config.search_terms")
   search_terms = [row.term for row in search_terms_df.collect()]
   query_string = " OR ".join(search_terms) + " lang:en -is:retweet"
   ```

2. **API Call**:
   ```python
   params = {
       "query": query_string,  # Uses your configured terms
       "max_results": 100
   }
   ```

### Testing New Terms

After adding new terms:

1. **Run seeding script** to update the table
2. **Run Twitter ingestion job** to fetch tweets
3. **Check logs** for the generated query string
4. **Monitor results** to see if terms are too broad/narrow

## Best Practices

### Term Selection

✅ **Good Terms:**
- Specific products/technologies: "Claude", "Gemini", "Databricks"
- Well-known acronyms: "LLM", "ML", "AI"
- Trending topics: "AI Driven Development"

❌ **Avoid:**
- Too generic: "technology", "software" (too much noise)
- Too specific: "databricks-connect-v2.1.3" (too few results)
- Ambiguous: "Oracle" (database or company or prediction?)

### Categories

Use consistent categories for organization:
- `AI`: AI models and general AI topics
- `Tool`: Specific development tools
- `Database`: Database technologies
- `Trend`: Industry trends and movements
- `Company`: Company-specific news
- `Custom`: Your custom categories

### Active Management

- Start with terms `active = true`
- Monitor tweet quality from each term
- Deactivate terms that produce low-quality results
- Review and adjust monthly

## Troubleshooting

### Table Doesn't Exist

**Error:** `Table or view 'main.config.search_terms' not found`

**Solution:**
```bash
# Run seeding script
./scripts/seed_config.sh
# Then run the notebook in Databricks UI
```

### No Search Terms Found

**Error:** In ingestion logs: `No search terms found in config table`

**Solution:**
```sql
-- Check if table is empty
SELECT COUNT(*) FROM main.config.search_terms;

-- Check if any active terms
SELECT COUNT(*) FROM main.config.search_terms WHERE active = true;

-- If empty, re-run seeding script
```

### Query String Too Long

**Warning:** `Query string exceeds Twitter API limit of 512 characters`

**Solution:**
```sql
-- Count active terms
SELECT COUNT(*) as active_terms
FROM main.config.search_terms
WHERE active = true;

-- Deactivate less important terms
UPDATE main.config.search_terms
SET active = false
WHERE category = 'less_important_category';
```

### Duplicate Terms

**Error:** `Duplicate key value violates unique constraint`

**Solution:**
```sql
-- Check for duplicates
SELECT term, COUNT(*)
FROM main.config.search_terms
GROUP BY term
HAVING COUNT(*) > 1;

-- Remove duplicates (keep most recent)
-- First, backup the table
CREATE TABLE main.config.search_terms_backup AS
SELECT * FROM main.config.search_terms;

-- Then use seeding script which handles duplicates via merge
```

## Advanced Usage

### Different Term Sets for Different Times

```sql
-- Weekend terms (lighter topics)
UPDATE main.config.search_terms
SET active = CASE
    WHEN category IN ('Entertainment', 'Fun') THEN true
    ELSE false
END
WHERE dayofweek(current_date()) IN (1, 7);  -- Sunday, Saturday
```

### A/B Testing Terms

```sql
-- Create test group
ALTER TABLE main.config.search_terms ADD COLUMN test_group STRING;

UPDATE main.config.search_terms
SET test_group = 'control'
WHERE term IN ('Claude', 'Databricks');

UPDATE main.config.search_terms
SET test_group = 'experiment'
WHERE term IN ('AI Assistant', 'Data Platform');

-- Activate only one group
UPDATE main.config.search_terms
SET active = (test_group = 'experiment');
```

## Backup and Restore

### Backup

```sql
CREATE TABLE main.config.search_terms_backup AS
SELECT * FROM main.config.search_terms;
```

### Restore

```sql
DELETE FROM main.config.search_terms;

INSERT INTO main.config.search_terms
SELECT * FROM main.config.search_terms_backup;
```

## Related Documentation

- [Twitter API Search Operators](https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query)
- [Twitter Ingestion Script](src/twitter_ingestion_script.py)
- [Bot Detection](BOT_DETECTION.md)
