# Product Requirements Document (PRD)  
**Product Name:** AI Signal – Daily & Weekly AI/Data Newsletter  
**Version:** 1.0  
**Date:** December 2025  
**Owner:** [Your Name/Team]  
**Status:** Draft for internal alignment

### 1. Business Context & Problem Statement

Professionals in AI, machine learning, and data engineering are drowning in noise. Every day thousands of tweets and LinkedIn posts are published about new models, benchmarks, tools, and companies, but:

- 95 % is repetitive, low-signal, or promotional  
- The 5 % that actually matters (new model releases, major benchmarks, architecture breakthroughs, funding announcements, controversial takes from credible builders) is scattered and hard to find  
- Existing newsletters are either weekly (too slow), human-curated (don’t scale), or low quality (AI slop)

**We lose hours every week trying to stay on top of what actually moved the industry yesterday.**

AI Signal solves this by delivering a **zero-fluff, high-signal daily and weekly newsletter** that surfaces only the 5–12 most important stories of the day/week in the AI & data engineering ecosystem, automatically curated from real-time X/Twitter (and later LinkedIn) using a Databricks-native pipeline + LLM agent.

### 2. Goal & Vision

**Vision**  
Become the single source of truth that every AI practitioner, data engineer, and engineering leader opens first every morning to know “what actually happened yesterday in AI”.

**Primary Business Goal (12 months)**  
Reach 25,000 active subscribers with ≥48 % open rate and ≥12 % click-through rate on the daily edition (top-decile newsletter performance).

### 3. Success Metrics

| Metric                          | Target (MVP → 6 mo → 12 mo)         | Definition                                                                 |
|---------------------------------|-------------------------------------|----------------------------------------------------------------------------|
| Daily Active Subscribers        | 100 → 5,000 → 25,000+              | Unique opens in last 30 days                                               |
| Average Open Rate (Daily)       | ≥50 % → ≥48 % → ≥45 %              | Industry top-decile is ~45–50 %                                            |
| Click-Through Rate (Daily)      | ≥15 % →14 % →12 %                   | Clicks on story links / deliveries                                         |
| Retention (30-day)              | ≥70 %                              | % of subscribers still opening after 30 days                               |
| Delivery Reliability            | 100 %                              | Newsletter sent every day (Mon–Sat) and every Monday (weekly) on time      |
| Pipeline Latency                | <4 hours                           | From tweet posted → appears in that day’s newsletter                       |
| False Positive Rate (spam/low-quality stories) | ≤5 %                     | Manually reviewed % of stories readers would consider noise                |
| Cost per 1,000 deliveries       | ≤$0.012                            | Full stack cost (Databricks + LLM + email)                                 |

### 4. User Personas

| Persona                        | Job Title                              | Pain Point                                      |
|--------------------------------|----------------------------------------|-------------------------------------------------|
| AI Researcher / ML Engineer    | Researcher, Applied Scientist          | Misses new model releases & benchmark papers    |
| Data Engineer / MLOps          | Data Engineer, Platform Engineer       | Needs to know new Databricks features fast      |
| Engineering Leader             | VP Eng, Head of AI, CTO                | Needs 5-min executive summary of the week       |
| Indie Hacker / Founder     | Building in AI, needs to spot trends early      |

### 5. Core User Stories (MVP)

| Priority | As a…                          | I want to…                                               | So that…                                              |
|----------|--------------------------------|----------------------------------------------------------|-------------------------------------------------------|
| P0       | Subscriber                     | Receive a clean, markdown/HTML email every morning (Mon–Sat) with 5–12 top stories | I know what mattered yesterday in <5 min               |
| P0       | Subscriber                     | Receive a longer, deeper weekly edition every Monday     | I can forward the definitive recap to my team          |
| P0       | Newsletter Owner               | Add/remove search terms (e.g., “o1”, “deepseek”, “photon”) without code changes | We stay up-to-date with new models & tools             |
| P1       | Subscriber                     | Click a story and land directly on the original tweet    | I can read replies and context                          |
| P1       | Subscriber                     | See author credibility (followers + verification)        | I can judge signal vs hype                             |
| P2       | Subscriber                     | Get a plain-text version (for email clients that hate HTML) | I can read it anywhere                                |

### 6. Functional Requirements (MVP)

1. Configurable search term list (stored in Delta table or feature flags)
2. Daily ingestion of English-language tweets containing any search term (min engagement filter)
3. Deduplicated, enriched bronze → silver → gold Delta tables in Unity Catalog
4. Daily materialised view of top ~100 candidate tweets (by influence score)
5. LLM agent (Mosaic AI or external) that:
   - Filters out noise, promo, duplicates
   - Writes 1-sentence headline + 2–3 sentence summary per story
   - Ranks final 5–12 stories
6. Automated generation of daily & weekly markdown → HTML newsletter
7. Delivery via email provider (Beehiiv, ConvertKit, or Resend) at 07:30 UTC daily
8. Basic admin dashboard (Databricks SQL) showing pipeline health and story log

### 7. Non-Functional Requirements

- End-to-end latency <4 hours (tweet → newsletter)
- System must handle 50k+ tweets/day without backlog
- 99.9 % pipeline uptime (Mon–Sat)
- All secrets (Twitter bearer, LLM keys, email API) in Databricks Secret Scope
- Cost monitoring dashboard

### 8. Explicitly Out of Scope (MVP & v1)

| Feature                                      | Reason out of scope                                      |
|----------------------------------------------|---------------------------------------------------------------------|
| LinkedIn ingestion                           | No reliable public API or compliant scraping path at scale         |
| Real-time (<15 min) newsletter               | Too expensive and unnecessary — daily cadence is sufficient        |
| User personalization / custom topics         | Adds huge complexity; will be v2+                                   |
| Mobile app                                   | Focus on best-in-class email experience first                       |
| Comments/section for reader discussion       | Will use X/Twitter thread replies instead                           |
| Paid tier or sponsorships                    | Will remain free until >20k subscribers                             |
| Multilingual support                         | English-only for MVP (90 %+ of high-signal content)                 |
| Video or podcast version                     | Future format once written newsletter is perfected                  |
| Manual human editing step                    | Defeats automation goal                                           |

### 9. Risks & Mitigations

| Risk                                          | Mitigation                                              |
|-----------------------------------------------|---------------------------------------------------------|
| Twitter API access revoked or too expensive   | Start with v2 Elevated access; budget for Enterprise if needed |
| LLM hallucination or low-quality summaries    | Human-in-the-loop review for first 30 days + prompt iteration   |
| Spam complaints → email deliverability issues | Use reputable ESP, double opt-in, easy unsubscribe              |

This PRD now serves as the single source of truth for the MVP.  
Next steps: Technical Design Doc → 2-week spike → Build.

Let me know if you’d like me to generate the Technical Design Doc or the Beehiiv/Resend integration plan next!