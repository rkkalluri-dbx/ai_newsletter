# Product Requirements Document (PRD)
## Reliability Project Workflow Tracker

**Version:** 1.0
**Date:** November 30, 2024
**Author:** Product Management
**Status:** Draft - Awaiting Approval

---

## 1. Problem & Opportunity

### Core Problem

Georgia Power's Reliability team manages 700+ capital projects annually across 15 vendors using a spreadsheet-based tracking system. With projects cycling through multiple stages (authorization, vendor design, QA/QC review, revisions, construction, completion), critical projects frequently "fall through the cracks"—particularly when returned to vendors for corrections. The current process lacks automated visibility, proactive alerting, and vendor accountability metrics.

### Current State

- **Data Management:** Spreadsheet maintained manually by Lance and Burton
- **Reporting:** Power BI dashboard pulling from on-prem SQL Server
- **Data Sources:** Jets database, Sprint, manual entry
- **Vendor Management:** 15 vendors with bi-weekly meetings
- **Project Volume:** 700+ projects annually (growing)

### Business Opportunity

Solving this problem directly addresses reliability and customer experience goals. When projects are delayed or lost in the workflow, preventable outages occur. By implementing an automated workflow tracking system with intelligent alerts and vendor performance visibility, the team can:

- Reduce project cycle time
- Prevent reliability incidents caused by delayed capital improvements
- Hold vendors accountable through measurable SLAs
- Enable the team to manage growing project volumes without proportional staffing increases

---

## 2. Goals & Success Metrics

### Primary Goals

1. **Eliminate projects falling through the cracks** — Ensure 100% of projects have tracked status visibility with automated alerts for overdue milestones
2. **Improve vendor accountability** — Provide measurable vendor performance metrics for bi-weekly vendor meetings

### Key Performance Indicators (KPIs)

| KPI | Current State | Target |
|-----|---------------|--------|
| Projects with overdue milestones undetected for >7 days | Unknown (manual tracking) | 0 |
| Average time to identify stalled projects | Days/weeks | <24 hours (automated) |
| Vendor performance visibility | None | 100% of vendors tracked |
| Manual spreadsheet data entry touchpoints | Multiple columns | Reduce by 80% |

---

## 3. Scope & Out of Scope

### In Scope (MVP)

- **Workflow status dashboard** showing all projects by stage (Authorization → Design → QA/QC → Construction → Complete)
- **Gantt chart / timeline view** for project scheduling visibility using Gantt-Task-React
- **Automated alerts/notifications** via Databricks Jobs when projects exceed expected stage duration
- **Vendor performance metrics** (on-time delivery rates, revision turnaround times) visualized with Recharts
- **"Next actions" view** — prioritized list of projects requiring follow-up
- **Integration with existing data sources** (Jets database, existing SQL Server, Databricks Lakebase)
- **Southern Company branded UI** using Material-UI with corporate design system

### Out of Scope

- **Third-party licensed solutions** (e.g., Primavera P6)
- **Mobile native application** — React web app is sufficient for MVP
- **Automated vendor communication** (email/SMS) — manual outreach during bi-weekly meetings preferred
- **Financial/budgeting module** — project cost tracking not part of initial scope
- **Legacy Power BI dashboard maintenance** — new system replaces existing dashboard

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Flask (Python), SQLAlchemy | REST API, business logic, ORM |
| **Database** | PostgreSQL (Databricks Lakebase) | Persistent storage, version-controlled project data |
| **Frontend** | React 18, Material-UI | SPA with Southern Company branding |
| **Visualization** | Recharts, Gantt-Task-React | Charts, metrics dashboards, timeline views |
| **Deployment** | Databricks Asset Bundles (DABs) | Infrastructure-as-code, CI/CD |
| **Hosting** | Databricks Apps | Managed application hosting |
| **Automation** | Databricks Jobs | Scheduled alerts, data sync, notifications |

---

## 5. User Stories (MVP)

### US-1: Overdue Project Visibility
**As a** reliability analyst,
**I want to** see all projects that have been sent to vendors and not returned within the expected window,
**So that** I can follow up before they fall through the cracks.

**Acceptance Criteria:**
- Dashboard displays projects exceeding SLA thresholds
- Projects are sorted by days overdue (most critical first)
- Visual indicator (red/yellow/green) shows urgency level

---

### US-2: Gantt Chart Timeline View
**As a** reliability supervisor,
**I want to** see a Gantt chart view of project timelines,
**So that** I can quickly understand the overall project pipeline and identify bottlenecks.

**Acceptance Criteria:**
- Interactive Gantt chart showing all active projects
- Ability to zoom in/out on timeline (week/month/quarter)
- Color-coded by project stage
- Click-through to project details

---

### US-3: Automated Overdue Alerts
**As a** reliability analyst,
**I want to** receive automated alerts when a project milestone is overdue,
**So that** I don't have to manually check 700+ projects for issues.

**Acceptance Criteria:**
- Daily automated job checks all project milestones
- Alerts generated for projects exceeding configurable thresholds
- Alert summary available in dashboard "notifications" area
- Future: Email notification capability

---

### US-4: Vendor Performance Metrics
**As a** reliability manager,
**I want to** see vendor performance metrics (timeliness, revision rates),
**So that** I can provide feedback during bi-weekly vendor meetings.

**Acceptance Criteria:**
- Vendor scorecard showing on-time delivery rate
- Average turnaround time per vendor
- Revision/rework rate per vendor
- Trend charts (improving/declining performance)

---

### US-5: Next Actions Priority List
**As a** reliability analyst,
**I want to** see a prioritized "next actions" list when I open the dashboard,
**So that** I know which projects need my attention first.

**Acceptance Criteria:**
- Top 10 priority actions displayed on dashboard home
- Actions ranked by urgency and business impact
- One-click navigation to project details
- Ability to mark actions as "addressed"

---

### US-6: Filtering and Search
**As a** reliability supervisor,
**I want to** filter projects by vendor, status, and date range,
**So that** I can prepare for specific vendor meetings.

**Acceptance Criteria:**
- Multi-select filters for vendor, status, region
- Date range picker for authorization/completion dates
- Save filter presets for recurring reports
- Export filtered results to CSV

---

### US-7: Enterprise Data Storage
**As a** reliability manager,
**I want to** project data to be stored in an enterprise-grade system (PostgreSQL on Databricks Lakebase),
**So that** data is version-controlled, auditable, and recoverable.

**Acceptance Criteria:**
- All project data persisted in PostgreSQL
- Audit trail for all data changes (who, when, what)
- Daily automated backups
- Data recoverable in case of system failure

---

### US-8: Automated Data Sync
**As a** reliability analyst,
**I want to** the system to auto-populate project data from existing databases (Jets, SQL Server),
**So that** I minimize manual data entry.

**Acceptance Criteria:**
- Scheduled sync job pulls data from Jets database
- Work order numbers automatically trigger data enrichment
- Manual entry required only for non-automated fields
- Sync status/errors visible in admin panel

---

## 6. Evidence (Verbatim Quotes from Transcript)

### Quote 1: Core Problem
> *"If you look at all the projects we have, so you got 710 projects and Burton and Lance? They're really good, but it's tough, right, for them to keep up with that amount of projects because, you know, we may send 20 back to make revisions on. And I would just love some type of, you know, software programming to kind of help us out in that aspect."*
>
> — **Gerald Ramsey**, Reliability & Automation Manager

### Quote 2: Project Visibility Need
> *"We could develop some type of Gantt chart or just scheduling tools to kind of show us... and quickly identify. Okay, this project has been sent out to a vendor. We haven't received it back yet, you know, just quickly identify those so we can follow back up with that vendor."*
>
> — **Gerald Ramsey**

### Quote 3: Vendor Accountability
> *"Maybe even some metrics around, you know, the timeliness of us getting these projects back... that has just kind of helped us know, you know, which vendors are performing well for us and which ones we may need to, you know, provide feedback to."*
>
> — **Gerald Ramsey**

### Quote 4: Business Impact
> *"The financial impact of not getting projects into construction — it's a reliability impact. It's an efficiency impact. This affects the customer experience, right? If we're not getting these projects completed on time and things fall through the cracks. Well, you know, that's maybe an outage that we could have prevented come to fruition."*
>
> — **Gerald Ramsey**

### Quote 5: Build vs. Buy Preference
> *"I would say if we could build something that the team can use that we can maintain going forward... I probably want to stay away from, like, having to get licenses and things of that nature."*
>
> — **Gerald Ramsey**

---

## 7. Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Reliability & Automation Manager | Gerald Ramsey | Executive sponsor, requirements owner |
| Reliability Supervisor | Burton Law | Day-to-day user, workflow owner |
| Reliability Program Manager | Lance Boyer | Day-to-day user, process owner |
| Apex Solutions Architect | Raj | Technical solution design |
| Apex Account Lead | Lindsay | Project coordination |

---

## 8. Open Questions

1. **Data Sync Frequency:** How often should the system sync with Jets database? (Real-time vs. hourly vs. daily)
2. **Alert Thresholds:** What are the specific SLA windows for each project stage before an alert is triggered?
3. **User Authentication:** Will the app use Southern Company SSO/Active Directory integration?
4. **Historical Data:** How much historical project data should be migrated into the new system?
5. **Notification Channels:** Beyond dashboard alerts, are email notifications required for MVP?

---

## 9. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Technical Lead | | | |
| Stakeholder | Gerald Ramsey | | |

---

**Status:** Awaiting Approval
**Next Steps:** Upon approval, proceed to technical specification and architecture design.
