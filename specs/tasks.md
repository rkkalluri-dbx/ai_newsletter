# tasks.md — The TO-DO
## Reliability Project Workflow Tracker

**Version:** 1.0
**Last Updated:** November 30, 2024
**Source:** [plan.md](./plan.md)

---

## Phase 1: Setup & Foundation

### 1.1 Project Initialization
- [x] **TASK-001**: Create GitHub repository `gpc-reliability-tracker`
- [x] **TASK-002**: Initialize Flask backend with app factory pattern
- [x] **TASK-003**: Initialize React frontend with Vite + TypeScript
- [x] **TASK-004**: Configure ESLint, Prettier, and pre-commit hooks
- [x] **TASK-005**: Create initial `databricks.yml` DABs configuration
- [x] **TASK-006**: Set up GitHub Actions CI pipeline (lint, test, build)

### 1.2 Database Setup (Delta Lake + Unity Catalog)
- [x] **TASK-007**: ~~Create PostgreSQL database in Databricks Lakebase~~ → Create Unity Catalog schema for Delta tables
- [x] **TASK-008**: ~~Configure SQLAlchemy connection~~ → Configure Databricks SQL Connector with Unity Catalog
- [x] **TASK-009**: Create Delta table for `vendors` in Unity Catalog
- [x] **TASK-010**: Create Delta table for `projects` in Unity Catalog
- [x] **TASK-011**: Create Delta table for `milestones` in Unity Catalog
- [x] **TASK-012**: Create Delta table for `alerts` in Unity Catalog
- [x] **TASK-013**: Create Delta table for `audit_logs` in Unity Catalog
- [x] **TASK-014**: Create Delta table for `vendor_metrics` in Unity Catalog
- [x] **TASK-015**: Seed database with 15 vendor records
- [x] **TASK-016**: Seed database with sample project data (50 records)
- [x] **TASK-016A**: Seed milestones for each project (6 milestones per project matching lifecycle stages)
- [x] **TASK-016B**: Seed alerts with mix of severities (info/warning/critical) and acknowledged states
- [x] **TASK-016C**: Seed audit_logs with sample change history (status transitions, date updates)
- [x] **TASK-016D**: Seed vendor_metrics with 3 months of historical performance data per vendor
- [x] **TASK-016E**: Create seed data script with realistic distribution (30% on-track, 40% warning, 30% critical)
- [x] **TASK-016F**: Add CLI command to reset and reseed database for development/demo

### 1.3 Backend Foundation
- [x] **TASK-017**: Create SQLAlchemy model: `Vendor`
- [x] **TASK-018**: Create SQLAlchemy model: `Project`
- [x] **TASK-019**: Create SQLAlchemy model: `Milestone`
- [x] **TASK-020**: Create SQLAlchemy model: `Alert`
- [x] **TASK-021**: Create SQLAlchemy model: `AuditLog`
- [x] **TASK-022**: Create SQLAlchemy model: `VendorMetric`
- [x] **TASK-023**: Implement base Flask error handlers (400, 404, 500)
- [x] **TASK-024**: Implement standard API response envelope utility
- [x] **TASK-025**: Configure CORS for frontend origin

### 1.4 Frontend Foundation
- [x] **TASK-026**: Install Material-UI and configure theme provider
- [x] **TASK-027**: Create Southern Company color palette in theme
- [x] **TASK-028**: Create app shell layout (Header, Sidebar, Main content)
- [x] **TASK-029**: Set up React Router with route definitions
- [ ] **TASK-030**: Create API client service with Axios
- [ ] **TASK-031**: Configure React Query provider and default options
- [ ] **TASK-032**: Create Zustand store for UI state (sidebar, filters)

---

## Phase 2: Core Features

### 2.1 Project List (FR-1.1, FR-1.2, FR-1.3)
- [x] **TASK-033**: Implement `GET /api/v1/projects` endpoint with pagination
- [x] **TASK-034**: Add query params: `status`, `vendor_id`, `region`, `priority`
- [x] **TASK-035**: Add query params: `date_from`, `date_to`, `search`
- [x] **TASK-036**: Add query params: `sort_by`, `sort_order`
- [x] **TASK-037**: Create `useProjects` React Query hook
- [x] **TASK-038**: Create `<ProjectsTable>` component with MUI DataGrid
- [ ] **TASK-039**: Create `<FilterPanel>` component with multi-select dropdowns
- [ ] **TASK-040**: Create `<SearchInput>` component with debounce
- [ ] **TASK-041**: Create Projects list page integrating all components
- [ ] **TASK-042**: Add URL query param sync for shareable filter state

### 2.2 Project Detail (FR-1.4, FR-1.5, FR-6.2, FR-6.5, FR-6.6)
- [ ] **TASK-043**: Implement `GET /api/v1/projects/{id}` endpoint
- [ ] **TASK-044**: Implement `PATCH /api/v1/projects/{id}` endpoint
- [ ] **TASK-045**: Implement `GET /api/v1/projects/{id}/history` endpoint
- [ ] **TASK-046**: Create audit log insertion on project update
- [ ] **TASK-047**: Create `useProject` React Query hook
- [ ] **TASK-048**: Create `<ProjectHeader>` component (title, status chip)
- [ ] **TASK-049**: Create `<ProjectInfoCard>` component (metadata display)
- [ ] **TASK-050**: Create `<ProjectTimeline>` component (milestone stepper)
- [ ] **TASK-051**: Create `<AuditHistoryTable>` component
- [ ] **TASK-052**: Create Project detail page with edit form
- [ ] **TASK-053**: Implement status transition validation in backend
- [ ] **TASK-053A**: Add `version` column to projects table migration
- [ ] **TASK-053B**: Implement version check in `PATCH /api/v1/projects/{id}` (optimistic locking)
- [ ] **TASK-053C**: Return 409 Conflict with changed fields when version mismatch
- [ ] **TASK-053D**: Create `<ConflictDialog>` component showing diff and current values
- [ ] **TASK-053E**: Add version to project edit form submission

### 2.3 Dashboard Summary (FR-2.2, FR-2.4, FR-2.6)
- [x] **TASK-054**: Implement `GET /api/v1/dashboard/summary` endpoint
- [x] **TASK-055**: Implement `GET /api/v1/dashboard/next-actions` endpoint
- [x] **TASK-056**: Create `useDashboardSummary` React Query hook
- [x] **TASK-057**: Create `<SummaryCard>` component (metric + icon)
- [x] **TASK-058**: Create `<NextActionsList>` component
- [x] **TASK-059**: Create `<StatusBarChart>` component with Recharts
- [x] **TASK-060**: Create Dashboard page layout with grid
- [x] **TASK-061**: Add click handlers to navigate from actions to project

### 2.4 CSV Export (FR-1.6)
- [x] **TASK-062**: Implement `GET /api/v1/projects/export` endpoint
- [x] **TASK-063**: Generate CSV with: work_order, vendor, status, dates, days_overdue
- [x] **TASK-064**: Add Export button to Projects page
- [x] **TASK-065**: Trigger file download on button click

### 2.5 Manual Data Entry (FR-5.7, FR-5.8) - POC Scope
- [ ] **TASK-065A**: Implement `POST /api/v1/projects` endpoint for manual project creation
- [ ] **TASK-065B**: Create `<ProjectCreateForm>` component with all required fields
- [ ] **TASK-065C**: Add "New Project" button to Projects page header
- [ ] **TASK-065D**: Implement form validation matching project schema
- [ ] **TASK-065E**: Implement `POST /api/v1/projects/import` endpoint for CSV upload
- [ ] **TASK-065F**: Create `<CSVImportDialog>` component with file picker
- [ ] **TASK-065G**: Implement CSV parsing and validation (work_order, vendor, dates)
- [ ] **TASK-065H**: Display import preview with error highlighting
- [ ] **TASK-065I**: Add "Import CSV" button to Projects page header

---

## Phase 3: Visualization

### 3.1 Gantt Chart (FR-3.1 - FR-3.5)
- [x] **TASK-066**: Install and configure `gantt-task-react`
- [x] **TASK-067**: Implement `GET /api/v1/gantt` endpoint
- [x] **TASK-068**: Transform project data to Gantt task format
- [x] **TASK-069**: Create `<GanttToolbar>` component (zoom, filters)
- [x] **TASK-070**: Create `<GanttChart>` wrapper component
- [x] **TASK-071**: Implement zoom levels: Week, Month, Quarter, Year
- [x] **TASK-072**: Add status-based color coding to bars
- [x] **TASK-073**: Add "today" line marker
- [x] **TASK-074**: Add click handler to navigate to project detail
- [x] **TASK-075**: Create GanttView page

### 3.2 Vendor Performance (FR-4.1 - FR-4.4)
- [x] **TASK-076**: Implement `GET /api/v1/vendors` endpoint
- [x] **TASK-077**: Implement `GET /api/v1/vendors/{id}` endpoint
- [x] **TASK-078**: Implement `GET /api/v1/vendors/{id}/metrics` endpoint
- [x] **TASK-079**: Create `useVendors` React Query hook
- [x] **TASK-080**: Create `<VendorComparisonChart>` horizontal bar chart
- [x] **TASK-081**: Create `<VendorTable>` with sortable metrics columns
- [x] **TASK-082**: Create Vendors list page
- [x] **TASK-083**: Create `<VendorMetricCards>` component
- [x] **TASK-084**: Create `<VendorTrendChart>` line chart
- [x] **TASK-085**: Create Vendor detail page

---

## Phase 4: Automation

### 4.1 Data Sync Job (FR-5.1 - FR-5.4) *(Deferred - Post-POC)*

> **POC Note:** Per spec clarification, automated data sync is deferred. Manual entry and CSV import cover POC needs.

- [ ] ~~**TASK-086**: Create `jobs/data_sync.py` entry point~~ *Deferred*
- [ ] ~~**TASK-087**: Implement Jets database connection (JDBC)~~ *Deferred*
- [ ] ~~**TASK-088**: Implement SQL Server connection (JDBC)~~ *Deferred*
- [ ] ~~**TASK-089**: Create upsert logic for projects table~~ *Deferred*
- [ ] ~~**TASK-090**: Create sync log table and logging~~ *Deferred*
- [ ] ~~**TASK-091**: Implement 3x retry with exponential backoff~~ *Deferred*
- [ ] ~~**TASK-092**: Configure Databricks Job in `databricks.yml` (hourly)~~ *Deferred*
- [ ] ~~**TASK-093**: Test sync job in dev environment~~ *Deferred*

### 4.2 Alert Generation Job (FR-2.1, FR-2.3, FR-2.7)
- [ ] **TASK-094**: Create `jobs/alert_generator.py` entry point
- [ ] **TASK-095**: Implement SLA threshold configuration (JSON/env)
- [ ] **TASK-096**: Query active projects with milestone dates
- [ ] **TASK-097**: Calculate days overdue for each milestone
- [ ] **TASK-098**: Determine severity: info (approaching), warning (overdue), critical (7+ days)
- [ ] **TASK-099**: Create/update alerts (avoid duplicates)
- [ ] **TASK-100**: Log alert generation summary
- [ ] **TASK-101**: Configure Databricks Job in `databricks.yml` (daily 6 AM)
- [ ] **TASK-102**: Test alert job in dev environment

### 4.3 Metrics Calculation Job (FR-4.6)
- [ ] **TASK-103**: Create `jobs/metrics_calculator.py` entry point
- [ ] **TASK-104**: Calculate on-time delivery rate per vendor
- [ ] **TASK-105**: Calculate average turnaround days per vendor
- [ ] **TASK-106**: Calculate revision rate per vendor
- [ ] **TASK-107**: Upsert vendor_metrics for current period
- [ ] **TASK-108**: Configure Databricks Job in `databricks.yml` (daily 5 AM)
- [ ] **TASK-109**: Test metrics job in dev environment

### 4.4 Alerts UI (FR-2.4, FR-2.5)
- [x] **TASK-110**: Implement `GET /api/v1/alerts` endpoint
- [x] **TASK-111**: Implement `POST /api/v1/alerts/{id}/acknowledge` endpoint
- [x] **TASK-112**: Implement `POST /api/v1/alerts/acknowledge` (bulk)
- [x] **TASK-113**: Create `useAlerts` React Query hook
- [x] **TASK-114**: Create `<AlertsPanel>` component for dashboard
- [x] **TASK-115**: Create `<AlertBadge>` severity indicator component
- [x] **TASK-116**: Add acknowledge button with optimistic update
- [x] **TASK-117**: Add notification badge to header

---

## Phase 5: Polish & QA

### 5.1 Southern Company Branding
- [ ] **TASK-118**: Apply Southern Company primary blue (#0033A0)
- [ ] **TASK-119**: Apply Southern Company typography (Roboto)
- [ ] **TASK-120**: Add Southern Company logo to header
- [ ] **TASK-121**: Review all components for brand consistency
- [ ] **TASK-122**: Add loading skeletons to all data-fetching pages

### 5.2 Performance Optimization
- [ ] **TASK-123**: Add database indexes on frequently queried columns
- [ ] **TASK-124**: Implement API response caching (5 min TTL)
- [ ] **TASK-125**: Enable React Query stale-while-revalidate
- [ ] **TASK-126**: Lazy-load Gantt chart component
- [ ] **TASK-127**: Audit bundle size and code-split routes

### 5.3 Testing
- [ ] **TASK-128**: Write pytest unit tests for `ProjectService`
- [ ] **TASK-129**: Write pytest unit tests for `AlertService`
- [ ] **TASK-130**: Write pytest unit tests for `MetricsService`
- [ ] **TASK-131**: Write pytest integration tests for `/projects` endpoints
- [ ] **TASK-132**: Write Jest tests for `<ProjectsTable>` component
- [ ] **TASK-133**: Write Jest tests for `<GanttChart>` component
- [ ] **TASK-134**: Write Playwright E2E test: Dashboard flow
- [ ] **TASK-135**: Write Playwright E2E test: Project update flow
- [ ] **TASK-136**: Write Playwright E2E test: Gantt navigation flow
- [ ] **TASK-137**: Write Playwright E2E test: Vendor metrics flow
- [ ] **TASK-138**: Write Playwright E2E test: Alert acknowledgment flow
- [ ] **TASK-139**: Run Locust load test with 50 concurrent users

### 5.4 Documentation
- [x] **TASK-140**: Write README.md with setup instructions
- [x] **TASK-141**: Document API endpoints in OpenAPI spec
- [ ] **TASK-142**: Create user guide for reliability team
- [ ] **TASK-143**: Document DABs deployment process

### 5.5 Deployment
- [ ] **TASK-144**: Deploy to dev environment and smoke test
- [ ] **TASK-145**: Deploy to staging environment
- [ ] **TASK-146**: Conduct UAT with Burton and Lance
- [ ] **TASK-147**: Fix issues identified in UAT
- [ ] **TASK-148**: Deploy to production
- [ ] **TASK-149**: Configure production monitoring/alerts
- [ ] **TASK-150**: Handoff to GPC operations team

---

## Task Summary

| Phase | Tasks | Priority | Notes |
|-------|-------|----------|-------|
| Phase 1: Setup | TASK-001 to TASK-032 | P0 | Foundation |
| Phase 2: Core Features | TASK-033 to TASK-065I | P0 | +14 new tasks (manual entry, locking) |
| Phase 3: Visualization | TASK-066 to TASK-085 | P0 | Gantt + Vendor metrics |
| Phase 4: Automation | TASK-094 to TASK-117 | P0 | TASK-086-093 deferred (data sync) |
| Phase 5: Polish & QA | TASK-118 to TASK-150 | P1 | Branding, testing, deployment |

**Total Tasks:** 170 (150 original + 20 new)
**Deferred Tasks:** 8 (TASK-086 to TASK-093 - Post-POC data sync)

---

## GitHub Project Board Labels

| Label | Color | Description |
|-------|-------|-------------|
| `phase:setup` | `#0e8a16` | Phase 1 tasks |
| `phase:core` | `#1d76db` | Phase 2 tasks |
| `phase:viz` | `#5319e7` | Phase 3 tasks |
| `phase:automation` | `#fbca04` | Phase 4 tasks |
| `phase:polish` | `#d93f0b` | Phase 5 tasks |
| `type:backend` | `#b60205` | Flask/Python tasks |
| `type:frontend` | `#0052cc` | React tasks |
| `type:database` | `#006b75` | DB/migration tasks |
| `type:devops` | `#5319e7` | CI/CD/DABs tasks |
| `type:test` | `#c2e0c6` | Testing tasks |
| `priority:p0` | `#b60205` | Must have |
| `priority:p1` | `#fbca04` | Should have |
| `priority:p2` | `#c2e0c6` | Nice to have |
