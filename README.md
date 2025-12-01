# AI Signal - Daily & Weekly AI/Data Newsletter

An automated newsletter pipeline that delivers high-signal AI and data engineering news by ingesting Twitter data, processing it through a Databricks lakehouse architecture, and using LLM agents to curate the most important stories.

## Project Overview

AI Signal solves the noise problem in AI/ML news by automatically surfacing only the 5-12 most important stories each day from Twitter, using Databricks Asset Bundles for deployment and orchestration.

**Key Features:**
- Real-time Twitter data ingestion (15-minute intervals)
- Delta Lake bronze-silver-gold architecture
- Configurable search terms via Delta table
- LLM-powered story curation (planned)
- Automated daily and weekly newsletter delivery (planned)

## Architecture

```
Twitter API → Unity Catalog Volume → Bronze Delta → Silver Delta → Gold Views → LLM Agent → Newsletter
```

## Project Structure

```
.
├── databricks.yml           # Databricks Asset Bundle configuration
├── src/                     # Source code
│   ├── create_uc_volume.py         # T003: Create Unity Catalog volume
│   ├── twitter_ingestion_script.py # T004: Twitter API ingestion job
│   └── ingestion_job.py             # T005: Bronze Delta table processing
├── specs/                   # Project specifications
│   ├── tasks.md            # Epic breakdown and task tracking
│   ├── plan.md             # Implementation plan
│   └── spec.md             # Technical specifications
└── PRD.md                  # Product Requirements Document
```

## Epic Progress

### ✅ Epic 1: Configurable Search & Ingestion (Complete)
- [x] T001: Setup Databricks Asset Bundles project
- [x] T002: Create config.search_terms Delta table
- [x] T003: Create Unity Catalog Volume for raw tweets
- [x] T004: Twitter v2 API ingestion job (15-min schedule)
- [x] T005: Bronze Delta table with Auto Loader
- [x] T006: Minimum engagement filter with influence scoring

### 🚧 Epic 2: Data Pipeline (Bronze → Silver → Gold)
- [ ] T007: Silver table with deduplication and enrichment
- [ ] T008: Gold daily materialized view (top 100 candidates)
- [ ] T009: Gold weekly rollup view

### 📋 Epic 3: LLM Summarization Agent
- [ ] T010: Create Mosaic AI serving endpoint
- [ ] T011: Prompt template for story summarization
- [ ] T012: Agent job for story selection and writing

### 📋 Epic 4: Newsletter Rendering & Delivery
- [ ] T013: Jinja2/HTML template
- [ ] T014: Rendering job (markdown → HTML)
- [ ] T015: Beehiiv/Resend API integration
- [ ] T016: Scheduled delivery

### 📋 Epic 5: Observability & Admin
- [ ] T017: Databricks SQL dashboard
- [ ] T018: Pipeline failure alerting
- [ ] T019: Secret scope setup

## Deployment

### Prerequisites
- Databricks workspace with Unity Catalog enabled
- Databricks CLI installed and configured
- Twitter API v2 bearer token (Elevated or Academic access)

### Deploy to Databricks

```bash
# Validate the bundle
databricks bundle validate

# Deploy to default target
databricks bundle deploy

# Run specific jobs
databricks bundle run create_volume_job        # One-time setup
databricks bundle run twitter_ingestion_job    # Manual trigger
databricks bundle run ai_newsletter_bronze_job # Manual trigger
```

### Configuration

1. **Twitter API Credentials**: Store your Twitter bearer token in Databricks secrets:
   ```bash
   databricks secrets create-scope <scope-name>
   databricks secrets put-secret <scope-name> twitter_bearer_token
   ```

2. **Search Terms**: Configure search terms in the `config.search_terms` Delta table:
   ```sql
   CREATE TABLE IF NOT EXISTS main.config.search_terms (term STRING);
   INSERT INTO main.config.search_terms VALUES
     ('claude code'), ('databricks'), ('gemini'), ('llm');
   ```

## Jobs

### 1. Create Volume Job (`create_volume_job`)
- **Purpose**: One-time setup to create Unity Catalog volume
- **Schedule**: Manual/one-time execution
- **Output**: `main.default.ai_newsletter_raw_tweets` volume

### 2. Twitter Ingestion Job (`twitter_ingestion_job`)
- **Purpose**: Fetch tweets from Twitter API and land as JSON
- **Schedule**: Every 15 minutes
- **Output**: Raw JSON files in UC volume

### 3. Bronze Processing Job (`ai_newsletter_bronze_job`)
- **Purpose**: Read raw JSON, filter by engagement, write to Delta
- **Schedule**: Hourly
- **Output**: `ai_newsletter_bronze.tweets` Delta table

## Development

### Local Testing
```bash
# Run bundle validation
databricks bundle validate

# Deploy to dev environment
databricks bundle deploy --target dev
```

## Roadmap

- **v0.1** (Current): Basic ingestion pipeline with bronze layer
- **v0.2**: Silver/gold data transformations
- **v0.3**: LLM agent integration
- **v0.4**: Newsletter rendering and delivery
- **v1.0**: Full production launch with observability

## Success Metrics

| Metric | Target |
|--------|--------|
| Daily Active Subscribers | 100 → 25,000+ |
| Average Open Rate | ≥45-50% |
| Click-Through Rate | ≥12-15% |
| Pipeline Latency | <4 hours |
| False Positive Rate | ≤5% |

## Contributing

This is a personal project. For questions or suggestions, please open an issue.

## License

MIT License
