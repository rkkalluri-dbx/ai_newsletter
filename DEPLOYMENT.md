# Deployment Guide - AI Newsletter

This guide explains how to deploy and update the AI Newsletter Databricks Asset Bundle.

## Prerequisites

1. Databricks CLI installed (`databricks --version`)
2. Authenticated with your workspace (`databricks auth profiles`)
3. Unity Catalog enabled in your workspace
4. Twitter API bearer token stored in Databricks secrets

## Project Structure

```
ai_newsletter/
├── databricks.yml          # Bundle configuration
├── src/                    # Source code
│   ├── create_uc_volume.py
│   ├── twitter_ingestion_script.py
│   └── ingestion_job.py
└── DEPLOYMENT.md          # This file
```

## Deployment Workflow

### 1. Make Changes Locally

Edit any Python files in the `src/` directory or update `databricks.yml`:

```bash
# Example: Edit the ingestion script
code src/twitter_ingestion_script.py

# Or update the bundle configuration
code databricks.yml
```

### 2. Validate the Bundle

Always validate before deploying:

```bash
databricks bundle validate --target default --profile DEFAULT
```

Expected output:
```
Name: ai_newsletter
Target: default
Workspace:
  Host: https://dbc-2647a0d2-b28d.cloud.databricks.com
  User: rkalluri@gmail.com
  Path: /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default

Validation OK!
```

### 3. Deploy to Databricks

Deploy the bundle to your workspace:

```bash
databricks bundle deploy --target default --profile DEFAULT
```

This will:
- Upload your source files to `/Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files/`
- Create or update the three jobs:
  - `ai_newsletter_create_volume`
  - `ai_newsletter_twitter_ingestion`
  - `ai_newsletter_bronze_processing`
- Apply any configuration changes

### 4. Run Jobs

Run jobs manually or let them execute on schedule:

```bash
# One-time setup (only needed once)
databricks bundle run create_volume_job --profile DEFAULT

# Test ingestion manually
databricks bundle run twitter_ingestion_job --profile DEFAULT

# Test bronze processing manually
databricks bundle run ai_newsletter_bronze_job --profile DEFAULT
```

## Typical Development Workflow

### Scenario: Update Ingestion Logic

1. **Edit the code locally:**
   ```bash
   code src/twitter_ingestion_script.py
   # Make your changes
   ```

2. **Validate:**
   ```bash
   databricks bundle validate --target default --profile DEFAULT
   ```

3. **Deploy:**
   ```bash
   databricks bundle deploy --target default --profile DEFAULT
   ```

4. **Test:**
   ```bash
   databricks bundle run twitter_ingestion_job --profile DEFAULT
   ```

5. **Commit to git:**
   ```bash
   git add src/twitter_ingestion_script.py
   git commit -m "Update ingestion logic to handle XYZ"
   git push
   ```

### Scenario: Add a New Job

1. **Update databricks.yml:**
   ```yaml
   resources:
     jobs:
       new_job_name:
         name: ai_newsletter_new_job
         tasks:
           - task_key: run_new_script
             notebook_task:
               notebook_path: ./src/new_script.py
               source: WORKSPACE
   ```

2. **Create the script:**
   ```bash
   code src/new_script.py
   # Write your code
   ```

3. **Validate and deploy:**
   ```bash
   databricks bundle validate --target default --profile DEFAULT
   databricks bundle deploy --target default --profile DEFAULT
   ```

## Targets

The bundle supports multiple targets for different environments:

### Default (Development)
```bash
databricks bundle deploy --target default --profile DEFAULT
```
- Mode: development
- Workspace: https://dbc-2647a0d2-b28d.cloud.databricks.com

### Production
```bash
databricks bundle deploy --target prod --profile DEFAULT
```
- Mode: production
- Inherits workspace configuration from profile

## Troubleshooting

### "Validation OK" but deployment fails

Check that:
- Your Databricks profile is configured: `databricks auth profiles`
- You have permissions to create jobs in the workspace
- Unity Catalog is enabled

### Jobs not updating after deployment

1. Verify the deployment succeeded:
   ```bash
   databricks bundle deploy --target default --profile DEFAULT
   ```

2. Check the job configuration in the Databricks UI:
   - Go to Workflows
   - Find your jobs (ai_newsletter_*)
   - Verify the notebook path and cluster settings

3. Check the deployed files:
   ```bash
   databricks workspace list /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files --profile DEFAULT
   ```

### Bundle validation fails

Common issues:
- Syntax error in `databricks.yml` (check YAML formatting)
- Invalid cluster configuration
- Missing required fields

Run with verbose logging:
```bash
databricks bundle validate --target default --profile DEFAULT --debug
```

## Monitoring Deployments

After deployment, verify the changes:

1. **Check deployed files:**
   ```bash
   databricks workspace list /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files/src --profile DEFAULT
   ```

2. **View job definitions:**
   ```bash
   databricks jobs list --profile DEFAULT | grep ai_newsletter
   ```

3. **Check job runs:**
   ```bash
   databricks jobs runs list --profile DEFAULT
   ```

## Best Practices

1. **Always validate before deploying**
   ```bash
   databricks bundle validate --target default --profile DEFAULT
   ```

2. **Test changes in development target first**
   - Use `--target default` for testing
   - Use `--target prod` only after validation

3. **Commit working code to git**
   - Deploy → Test → Commit
   - Keep git history clean and meaningful

4. **Use version control for databricks.yml**
   - Track all configuration changes
   - Review changes before deploying

5. **Monitor job runs after deployment**
   - Check Databricks UI for any errors
   - Verify data is flowing correctly

## Quick Reference

```bash
# Validate configuration
databricks bundle validate --target default --profile DEFAULT

# Deploy changes
databricks bundle deploy --target default --profile DEFAULT

# Run a specific job
databricks bundle run <job_key> --profile DEFAULT

# Check deployment status
databricks workspace list /Workspace/Users/rkalluri@gmail.com/.bundle/ai_newsletter/default/files --profile DEFAULT

# View logs
# Go to Databricks UI → Workflows → Select job → View run details
```

## Next Steps

After successful deployment:
1. Monitor the scheduled jobs in the Databricks UI
2. Verify data is flowing into the bronze table
3. Check Unity Catalog for the created volume and tables
4. Move on to Epic 2: Data Pipeline (Silver/Gold layers)
