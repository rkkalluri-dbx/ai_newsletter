# Specification: AI Signal – Daily & Weekly AI/Data Newsletter (MVP)

## 1. Overview
**Problem Statement:**  
Professionals in AI, machine learning, and data engineering lose hours every week trying to stay on top of what actually moved the industry yesterday because 95 % of tweets/LinkedIn posts are repetitive, low-signal, or promotional, while the 5 % that matters is scattered and hard to find.

**Target Users:**  
- AI Researcher / ML Engineer  
- Data Engineer / MLOps Engineer  
- Engineering Leader (VP Eng, Head of AI, CTO)  
- Indie Hacker / AI Founder

## 2. User Stories

| Actor                | Action                                                                 | Goal                                                                                   | Source Quote (Evidence)                                                                                          |
|----------------------|------------------------------------------------------------------------|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| Subscriber           | Receive a clean, markdown/HTML email every morning (Mon–Sat) with 5–12 top stories | I know what mattered yesterday in <5 min                                               | "Receive a clean, markdown/HTML email every morning (Mon–Sat) with 5–12 top stories"                             |
| Subscriber           | Receive a longer, deeper weekly edition every Monday                   | I can forward the definitive recap to my team                                          | "Receive a longer, deeper weekly edition every Monday"                                                       |
| Newsletter Owner     | Add/remove search terms (e.g., “o1”, “deepseek”, “photon”) without code changes | We stay up-to-date with new models & tools                                             | "Add/remove search terms … without code changes"                                                                 |
| Subscriber           | Click a story and land directly on the original tweet                  | I can read replies and context                                                         | "Click a story and land directly on the original tweet"                                                          |
| Subscriber           | See author credibility (followers + verification)                     | I can judge signal vs hype                                                             | "See author credibility (followers + verification)"                                                              |
| Subscriber           | Get a plain-text version                                               | I can read it anywhere                                                                 | "Get a plain-text version (for email clients that hate HTML)"                                                    |

## 3. Functional Requirements

- [ ] Configurable search term list stored in Delta table or feature flags
- [ ] Daily ingestion of English-language tweets containing any configured search term with minimum engagement filter
- [ ] Deduplicated, enriched bronze → silver → gold Delta tables in Unity Catalog
- [ ] Daily materialized view of top ~100 candidate tweets ranked by influence score
- [ ] LLM agent that filters noise/promo/duplicates, writes 1-sentence headline + 2–3 sentence summary, and ranks final 5–12 stories
- [ ] Automated generation of daily (Mon–Sat) and weekly (Monday) newsletter in markdown → HTML
- [ ] Delivery via reputable email provider at 07:30 UTC daily
- [ ] Basic admin dashboard in Databricks SQL showing pipeline health and daily story log
- [ ] All secrets (Twitter bearer token, LLM keys, email API keys) stored in Databricks Secret Scope