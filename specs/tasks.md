# Epic Breakdown & Tasks – AI Signal MVP

## Epic 1: Configurable Search & Ingestion
- [x] T001 Setup barebones Databricks project for Databricks Asset Bundles deployment
- [x] T002 Create `config.search_terms` Delta table with terms: claude code, databricks, gemini, kiro (+ future ones)
- [x] T003 Create Unity Catalog Volume: main.default.ai_newsletter_raw_tweets
- [x] T004 Implement Twitter v2 Elevated/Academic bearer-token ingestion job (15-min schedule)
- [x] T005 Write raw JSON → bronze Delta table using Auto Loader or structured streaming
- [x] T006 Add minimum engagement filter (configurable, default min_faves:10 or calculated influence score)

## Epic 2: Data Pipeline (Bronze → Silver → Gold)
- [x] T007 Silver table: deduplication, lang=en filter, author enrichment, influence_score UDF
- [ ] T008 Gold daily materialized view: top 100 candidates per day by influence score
- [ ] T009 Gold weekly rollup view (last 7 days)

## Epic 3: LLM Summarization Agent
- [ ] T010 Create Mosaic AI serving endpoint or external Claude 3.5 Sonnet wrapper
- [ ] T011 Prompt template that outputs exactly: headline (1 sentence) + summary (2–3 sentences) + source URLs
- [ ] T012 Agent job (daily 06:00 UTC) that reads top 100 → outputs final 5–12 stories → writes to `gold.newsletter_stories`

## Epic 4: Newsletter Rendering & Delivery
- [ ] T013 Jinja2/HTML template for daily and weekly editions
- [ ] T014 Python job that renders markdown → HTML + plain-text versions
- [ ] T015 Integration with Beehiiv or Resend API
- [ ] T016 Scheduled delivery: daily 07:30 UTC, weekly Monday 07:30 UTC

## Epic 5: Observability & Admin
- [ ] T017 Databricks SQL dashboard: pipeline status, story log, cost monitoring
- [ ] T018 Alerting on pipeline failure or >5 % false-positive stories
- [ ] T019 Secret scope setup for all API keys

## Epic 6: Launch & Feedback Loop
- [ ] T020 Closed beta with 100 subscribers (manual CSV import)
- [ ] T021 Collect open-rate / CTR data after 2 weeks
- [ ] T022 Iterate prompt & filters until false-positive rate ≤5 %

Total estimated effort: 4–6 weeks for one experienced Databricks engineer.