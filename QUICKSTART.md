# Quick Start - AI Newsletter Development

## Daily Development Workflow

### 1. Edit Code Locally

```bash
# Edit any Python file in src/
code src/twitter_ingestion_script.py

# Make your changes...
```

### 2. Validate → Deploy → Test

```bash
# Validate the bundle
databricks bundle validate --target default --profile DEFAULT

# Deploy to Databricks
databricks bundle deploy --target default --profile DEFAULT

# Test the job (optional)
databricks bundle run twitter_ingestion_job --profile DEFAULT
```

### 3. Commit to Git

```bash
git add src/twitter_ingestion_script.py
git commit -m "Update ingestion logic"
git push
```

## Key Commands

```bash
# Validate configuration
databricks bundle validate --target default --profile DEFAULT

# Deploy all changes
databricks bundle deploy --target default --profile DEFAULT

# Run specific jobs
databricks bundle run create_volume_job --profile DEFAULT
databricks bundle run twitter_ingestion_job --profile DEFAULT
databricks bundle run ai_newsletter_bronze_job --profile DEFAULT

# Check deployed files
databricks workspace list /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files/src --profile DEFAULT

# List jobs
databricks jobs list --profile DEFAULT | grep ai_newsletter
```

## Project Structure

```
ai_newsletter/
├── databricks.yml          # Bundle configuration
├── src/                    # Python source code
│   ├── create_uc_volume.py         # T003: Unity Catalog volume
│   ├── twitter_ingestion_script.py # T004: Twitter ingestion (15min)
│   └── ingestion_job.py            # T005: Bronze processing (hourly)
├── specs/                  # Documentation
│   ├── tasks.md           # Epic breakdown
│   ├── plan.md            # Implementation plan
│   └── spec.md            # Technical specs
├── README.md              # Project overview
├── DEPLOYMENT.md          # Detailed deployment guide
└── QUICKSTART.md          # This file
```

## Example: Update Ingestion Logic

Let's say you want to change the minimum engagement filter:

```bash
# 1. Edit the file
code src/ingestion_job.py
# Change: min_faves_filter = 10 → min_faves_filter = 20

# 2. Validate
databricks bundle validate --target default --profile DEFAULT

# 3. Deploy
databricks bundle deploy --target default --profile DEFAULT

# 4. Test
databricks bundle run ai_newsletter_bronze_job --profile DEFAULT

# 5. Commit
git add src/ingestion_job.py
git commit -m "Increase engagement filter to 20 likes"
git push
```

## Deployed Jobs

| Job Name | Schedule | Purpose |
|----------|----------|---------|
| `ai_newsletter_create_volume` | Manual | Create Unity Catalog volume (one-time) |
| `ai_newsletter_twitter_ingestion` | Every 15 min | Fetch tweets from Twitter API |
| `ai_newsletter_bronze_processing` | Hourly | Process raw tweets into bronze Delta table |

## Current Status

✅ **Epic 1 Complete** (T001-T006)
- DAB project configured
- Twitter ingestion deployed
- Bronze Delta table processing active

🚧 **Next: Epic 2** (T007-T009)
- Silver table with deduplication
- Gold materialized views
- Weekly rollup aggregations

## Troubleshooting

**Problem:** Deployment fails
```bash
# Check validation first
databricks bundle validate --target default --profile DEFAULT

# Check authentication
databricks auth profiles
```

**Problem:** Jobs not updating
```bash
# Verify deployment succeeded
databricks bundle deploy --target default --profile DEFAULT

# Check deployed files
databricks workspace list /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files --profile DEFAULT
```

**Problem:** Job fails to run
- Check Databricks UI → Workflows → Select job → View logs
- Verify Unity Catalog access permissions
- Check secret scope for Twitter API token

## Next Steps

1. Monitor scheduled jobs in Databricks UI
2. Verify bronze table is being populated
3. Start Epic 2: Silver/Gold transformations
4. Review [DEPLOYMENT.md](DEPLOYMENT.md) for detailed workflow

## Resources

- **GitHub Repo:** https://github.com/rkkalluri-dbx/ai_newsletter
- **Databricks Workspace:** https://dbc-2647a0d2-b28d.cloud.databricks.com
- **Bundle Docs:** https://docs.databricks.com/dev-tools/bundles/
