# spec.md — The WHAT
## Reliability Project Workflow Tracker

**Version:** 1.0
**Last Updated:** November 30, 2024
**Source:** [PRD.md](../PRD.md)

---

## 1. Overview

A web-based application that enables Georgia Power's Reliability team to track 700+ capital projects across 15 vendors, replacing the current spreadsheet-based workflow with automated visibility, proactive alerting, and vendor accountability metrics.

### Primary Goals
1. Eliminate projects falling through the cracks (100% visibility with automated alerts)
2. Improve vendor accountability (measurable performance metrics for bi-weekly meetings)

### Success Metrics
| Metric | Target |
|--------|--------|
| Overdue projects undetected >7 days | 0 |
| Time to identify stalled projects | <24 hours |
| Vendor performance visibility | 100% |
| Reduction in manual data entry | 80% |

---

## Clarifications

### Session 2025-11-30
- Q: What are the valid project lifecycle stages and their expected sequence? → A: Authorized → Assigned to Vendor → Design Submitted → QA/QC → Approved → Construction Ready
- Q: What are the default SLA thresholds (in days) for each project stage? → A: Assigned to Vendor: 7 days, QA/QC: 7 days, Approved to Construction Ready: 3 days
- Q: How should the three user roles (Viewer, Editor, Admin) map to business roles? → A: Analyst, Supervisor, Manager all get Editor role; separate IT Admin role for Admin privileges
- Q: How should the system handle concurrent edits when two users modify the same project? → A: Optimistic locking with conflict warning if data changed since load
- Q: What should happen when data sync from Jets/SQL Server fails? → A: Sync deferred for POC; manual data entry only

---

## 2. User Stories

### US-1: Overdue Project Visibility
**As a** reliability analyst,
**I want to** see all projects that have been sent to vendors and not returned within the expected window,
**So that** I can follow up before they fall through the cracks.

**Acceptance Criteria:**
- [ ] Dashboard displays projects exceeding SLA thresholds
- [ ] Projects are sorted by days overdue (most critical first)
- [ ] Visual indicator (red/yellow/green) shows urgency level

---

### US-2: Gantt Chart Timeline View
**As a** reliability supervisor,
**I want to** see a Gantt chart view of project timelines,
**So that** I can quickly understand the overall project pipeline and identify bottlenecks.

**Acceptance Criteria:**
- [ ] Interactive Gantt chart showing all active projects
- [ ] Ability to zoom in/out on timeline (week/month/quarter)
- [ ] Color-coded by project stage
- [ ] Click-through to project details

---

### US-3: Automated Overdue Alerts
**As a** reliability analyst,
**I want to** receive automated alerts when a project milestone is overdue,
**So that** I don't have to manually check 700+ projects for issues.

**Acceptance Criteria:**
- [ ] Daily automated job checks all project milestones
- [ ] Alerts generated for projects exceeding configurable thresholds
- [ ] Alert summary available in dashboard "notifications" area

---

### US-4: Vendor Performance Metrics
**As a** reliability manager,
**I want to** see vendor performance metrics (timeliness, revision rates),
**So that** I can provide feedback during bi-weekly vendor meetings.

**Acceptance Criteria:**
- [ ] Vendor scorecard showing on-time delivery rate
- [ ] Average turnaround time per vendor
- [ ] Revision/rework rate per vendor
- [ ] Trend charts (improving/declining performance)

---

### US-5: Next Actions Priority List
**As a** reliability analyst,
**I want to** see a prioritized "next actions" list when I open the dashboard,
**So that** I know which projects need my attention first.

**Acceptance Criteria:**
- [ ] Top 10 priority actions displayed on dashboard home
- [ ] Actions ranked by urgency and business impact
- [ ] One-click navigation to project details
- [ ] Ability to mark actions as "addressed"

---

### US-6: Filtering and Search
**As a** reliability supervisor,
**I want to** filter projects by vendor, status, and date range,
**So that** I can prepare for specific vendor meetings.

**Acceptance Criteria:**
- [ ] Multi-select filters for vendor, status, region
- [ ] Date range picker for authorization/completion dates
- [ ] Save filter presets for recurring reports
- [ ] Export filtered results to CSV

---

### US-7: Enterprise Data Storage
**As a** reliability manager,
**I want to** project data stored in an enterprise-grade system,
**So that** data is version-controlled, auditable, and recoverable.

**Acceptance Criteria:**
- [ ] All project data persisted in PostgreSQL
- [ ] Audit trail for all data changes (who, when, what)
- [ ] Daily automated backups
- [ ] Data recoverable in case of system failure

---

### US-8: Automated Data Sync *(Deferred - Post-POC)*
**As a** reliability analyst,
**I want to** the system to auto-populate project data from existing databases,
**So that** I minimize manual data entry.

> **POC Note:** Deferred to post-POC. For POC, all project data will be entered manually or via CSV import.

**Acceptance Criteria:** *(Post-POC)*
- [ ] Scheduled sync job pulls data from Jets database
- [ ] Work order numbers automatically trigger data enrichment
- [ ] Manual entry required only for non-automated fields
- [ ] Sync status/errors visible in admin panel

---

## 3. Functional Requirements

### Project Lifecycle States
Projects progress through the following stages in sequence:
1. **Authorized** - Project approved and ready for vendor assignment
2. **Assigned to Vendor** - Work order sent to external contractor
3. **Design Submitted** - Vendor has submitted design deliverables
4. **QA/QC** - Internal quality review in progress
5. **Approved** - Design passed QA/QC review
6. **Construction Ready** - Final stage; ready for field execution

Each stage transition triggers SLA timer reset. Overdue detection (FR-2) applies per-stage thresholds.

**Default SLA Thresholds:**
| Stage Transition | SLA (Days) |
|------------------|------------|
| Authorized → Assigned to Vendor | N/A (internal scheduling) |
| Assigned to Vendor → Design Submitted | 7 |
| Design Submitted → QA/QC | N/A (immediate) |
| QA/QC → Approved | 7 |
| Approved → Construction Ready | 3 |

Thresholds are configurable per vendor via admin settings.

### FR-1: Project Management (US-1, US-6, US-7)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System SHALL display a paginated list of all projects with work order number, vendor, status, and days in current stage | P0 |
| FR-1.2 | System SHALL allow filtering projects by: vendor (multi-select), status (multi-select), region, priority, date range | P0 |
| FR-1.3 | System SHALL allow searching projects by work order number or description | P0 |
| FR-1.4 | System SHALL display project detail view with all metadata, milestones, and history | P0 |
| FR-1.5 | System SHALL allow authorized users to update project status and dates | P0 |
| FR-1.6 | System SHALL export filtered project list to CSV format | P1 |
| FR-1.7 | System SHALL save and recall filter presets per user | P2 |

### FR-2: Overdue Detection & Alerts (US-1, US-3, US-5)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System SHALL calculate days overdue for each project milestone based on configurable SLA thresholds | P0 |
| FR-2.2 | System SHALL display overdue projects with visual severity indicators (red >7 days, yellow 1-7 days, green on-track) | P0 |
| FR-2.3 | System SHALL run a daily batch job (6 AM ET) to generate alerts for overdue milestones | P0 |
| FR-2.4 | System SHALL display unacknowledged alerts in dashboard notification panel | P0 |
| FR-2.5 | System SHALL allow users to acknowledge/dismiss alerts | P0 |
| FR-2.6 | System SHALL generate "Next Actions" list ranked by: (a) days overdue, (b) priority, (c) vendor SLA | P0 |
| FR-2.7 | System SHALL escalate alert severity if milestone remains overdue after 7+ days | P1 |

### FR-3: Gantt Chart Visualization (US-2)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System SHALL display interactive Gantt chart with horizontal timeline and project bars | P0 |
| FR-3.2 | System SHALL allow zoom levels: Week, Month, Quarter, Year | P0 |
| FR-3.3 | System SHALL color-code project bars by current status | P0 |
| FR-3.4 | System SHALL show "today" marker on timeline | P0 |
| FR-3.5 | System SHALL navigate to project detail on bar click | P0 |
| FR-3.6 | System SHALL filter Gantt view by vendor, status, region | P1 |

### FR-4: Vendor Performance Metrics (US-4)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System SHALL calculate per-vendor: on-time delivery rate (%) | P0 |
| FR-4.2 | System SHALL calculate per-vendor: average turnaround days | P0 |
| FR-4.3 | System SHALL calculate per-vendor: revision rate (%) | P0 |
| FR-4.4 | System SHALL display vendor comparison bar chart | P0 |
| FR-4.5 | System SHALL display vendor trend line chart (3-6 month history) | P1 |
| FR-4.6 | System SHALL run daily batch job (5 AM ET) to pre-calculate metrics | P0 |
| FR-4.7 | System SHALL allow filtering metrics by time period (month/quarter/year) | P1 |

### FR-5: Data Integration & Sync (US-8) *(Deferred - Post-POC)*

> **POC Scope:** Manual data entry and CSV import only. Automated sync deferred to post-POC.

| ID | Requirement | Priority | POC Status |
|----|-------------|----------|------------|
| FR-5.1 | System SHALL sync project data from Jets database on hourly schedule | P0 | Deferred |
| FR-5.2 | System SHALL sync work order completion data from SQL Server on hourly schedule | P0 | Deferred |
| FR-5.3 | System SHALL match records by work_order_number as primary key | P0 | Deferred |
| FR-5.4 | System SHALL log all sync operations with record counts and errors | P0 | Deferred |
| FR-5.5 | System SHALL display sync status in admin panel | P1 | Deferred |
| FR-5.6 | System SHALL retry failed syncs up to 3 times with exponential backoff | P1 | Deferred |
| FR-5.7 | System SHALL allow manual project creation via form entry | P0 | **POC** |
| FR-5.8 | System SHALL allow bulk import of projects via CSV upload | P1 | **POC** |

### FR-6: Audit & Data Integrity (US-7)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | System SHALL log all data changes with: user_id, timestamp, field_changed, old_value, new_value | P0 |
| FR-6.2 | System SHALL display audit history on project detail page | P0 |
| FR-6.3 | System SHALL perform daily automated backups | P0 |
| FR-6.4 | System SHALL store data in PostgreSQL with referential integrity constraints | P0 |
| FR-6.5 | System SHALL implement optimistic locking using version column on project records | P0 |
| FR-6.6 | System SHALL display conflict warning when user saves stale data, showing changed fields and current values | P0 |

---

## 4. Non-Functional Requirements

### NFR-1: Performance
| ID | Requirement |
|----|-------------|
| NFR-1.1 | Page load time SHALL be < 2 seconds |
| NFR-1.2 | API response time SHALL be < 500ms (95th percentile) |
| NFR-1.3 | System SHALL support 50+ concurrent users |
| NFR-1.4 | Gantt chart SHALL render 500+ projects without degradation |

### NFR-2: Availability
| ID | Requirement |
|----|-------------|
| NFR-2.1 | System SHALL maintain 99.5% uptime during business hours (6 AM - 8 PM ET) |
| NFR-2.2 | Scheduled jobs SHALL complete within 15 minutes |

### NFR-3: Security
| ID | Requirement |
|----|-------------|
| NFR-3.1 | All traffic SHALL use HTTPS/TLS encryption |
| NFR-3.2 | System SHALL implement role-based access control (Viewer, Editor, Admin) |
| NFR-3.3 | System SHALL not store PII or credentials in application database |

**Role Mapping:**
| Application Role | Permissions | Business Roles |
|------------------|-------------|----------------|
| Viewer | Read-only access to dashboards and reports | (Future external stakeholders) |
| Editor | Full CRUD on projects, alerts, filters; export data | Reliability Analyst, Supervisor, Manager |
| Admin | Editor + system configuration, SLA thresholds, user management, sync settings | IT Administrator |

### NFR-4: Usability
| ID | Requirement |
|----|-------------|
| NFR-4.1 | UI SHALL conform to Southern Company brand guidelines |
| NFR-4.2 | UI SHALL be accessible on desktop browsers (Chrome, Edge, Firefox) |
| NFR-4.3 | UI SHALL meet WCAG 2.1 AA accessibility standards |

---

## 5. Out of Scope (POC)

The following are explicitly **NOT** included in this POC:

- Third-party licensed solutions (e.g., Primavera P6)
- Native mobile application
- Automated vendor communication (email/SMS)
- Financial/budgeting module
- Legacy Power BI dashboard maintenance
- SSO integration (basic auth for POC, SSO post-POC)
- **Automated data sync from Jets/SQL Server** (deferred; manual data entry for POC)

---

## 6. Glossary

| Term | Definition |
|------|------------|
| **Work Order** | Unique identifier for a capital project (e.g., WO-2024-001234) |
| **SLA** | Service Level Agreement - expected duration for a project stage |
| **Jets Database** | Source system containing project authorization data |
| **Milestone** | A checkpoint in the project lifecycle (e.g., "Design Received") |
| **Vendor** | External contractor responsible for project design work |
| **QA/QC** | Quality Assurance/Quality Control review stage |
