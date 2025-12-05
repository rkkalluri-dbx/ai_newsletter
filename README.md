# GPC Reliability Tracker

A web-based application that enables Georgia Power's Reliability team to track 700+ capital projects across 15 vendors, replacing the current spreadsheet-based workflow with automated visibility, proactive alerting, and vendor accountability metrics.

## Live Demo

- **Databricks App**: https://gpc-reliability-api-3268035903553121.1.azure.databricksapps.com
- **Local Development**: http://localhost:5001

---

## Demo Guide (25 minutes)

### Opening Hook (2 min)

**Start with the problem:**
> "Georgia Power manages over 700 capital projects annually across 15 vendors. Before this solution, Lance and Burton were tracking everything in spreadsheets. Projects would get sent to vendors for revisions and literally fall through the cracks - sometimes for weeks. When that happens, it's not just a process issue - it's a reliability issue that can cause preventable outages affecting customers."

**Quote from Gerald Ramsey (their manager):**
> "The financial impact of not getting projects into construction - it's a reliability impact. It's an outage that we could have prevented."

---

### Act 1: The Dashboard - Instant Visibility (5 min)

**Navigate to Dashboard**

**Talk through:**
1. **Summary Cards** - "Within seconds of logging in, Lance can see:
   - 50 active projects
   - 30 are overdue (red flag!)
   - 15 critical priority items need attention NOW"

2. **Status Distribution Chart** - "Visual breakdown of where projects are stuck - notice we have 14 in 'approved' but only 9 'construction ready' - that's a bottleneck"

3. **Next Actions Panel** - "This is the 'don't let things fall through the cracks' feature - prioritized list of what needs attention today"

4. **Alert Badge (top right)** - "13 unacknowledged alerts - click to see critical issues"

**Key message:** *"What used to take hours of spreadsheet filtering now takes 5 seconds"*

---

### Act 2: Drill Down - Project Detail (5 min)

**Click on a project from Next Actions**

**Walk through:**
1. **Project Header** - Work order, status chips, vendor, region
2. **Progress Bar** - Visual completion percentage
3. **Timeline Card** - Start date to target completion
4. **Milestones Tab** - "This is where projects used to get lost"
   - Show completed vs pending milestones
   - Highlight overdue ones in red
   - **Demo:** Click "Mark Complete" on a milestone (shows real-time update)

5. **History Tab** - "Full audit trail - who changed what and when"

6. **Edit Project** - Click button, show the form pre-populated
   - "Status changes, date updates - all tracked automatically"

**Key message:** *"Complete visibility into every project's journey"*

---

### Act 3: Vendor Accountability (4 min)

**Navigate to Vendors page**

**Talk through:**
1. **Vendor Performance Table** - "Before, they had no data for bi-weekly vendor meetings"
   - On-time percentage
   - Active projects per vendor
   - Sortable columns

2. **Click into a vendor** - Show their specific metrics
   - Historical performance trends
   - Which projects are assigned

**Key message:** *"Now they can have data-driven conversations: 'Pike Electric, your on-time rate dropped from 95% to 87% this quarter - what's happening?'"*

---

### Act 4: Proactive Alerts (3 min)

**Navigate to Alerts page**

**Show:**
1. **Severity Levels** - Critical (red), Warning (yellow), Info (blue)
2. **Alert Types** - Milestone overdue, approaching deadline, status changes
3. **Bulk Actions** - Acknowledge multiple alerts
4. **Click an alert** - Jumps directly to the project

**Key message:** *"The system watches 700+ projects so Lance and Burton don't have to"*

---

### Act 5: The Platform Story (3 min)

**Architecture highlights:**
- "Built entirely on Databricks platform"
- "Data stored in Delta Lake with Unity Catalog governance"
- "Deployed as a Databricks App - managed hosting, automatic scaling"
- "Same platform they'll use for future analytics and AI"

**Future possibilities:**
- "Predictive alerts - AI that predicts which projects will miss deadlines"
- "Automated data sync from Jets database and SQL Server"
- "Gantt chart visualization (coming soon)"

---

### Closing: The Impact (3 min)

**Before & After:**

| Metric | Before | After |
|--------|--------|-------|
| Time to identify stalled project | Days/Weeks | < 24 hours (automated) |
| Projects falling through cracks | Unknown | 0 (100% visibility) |
| Vendor performance data | None | Real-time metrics |
| Manual spreadsheet updates | Hours/week | Minutes |

**Return to the quote:**
> "If we're not getting these projects completed on time and things fall through the cracks - that's maybe an outage that we could have prevented."

**Close with:**
> "This solution ensures no project falls through the cracks. Every milestone tracked. Every vendor accountable. Every potential outage prevented."

---

### Demo Tips

1. **Have test data ready** - Projects with overdue milestones, mix of statuses
2. **Practice the milestone completion** - It's a satisfying real-time update
3. **Keep browser zoomed to 100%** - UI looks best
4. **Have a backup** - Local app at localhost:5001 if Databricks has issues
5. **Prepare for questions about:**
   - Data sources (Jets, SQL Server - planned integration)
   - Mobile access (responsive web, no native app needed)
   - Security (Databricks SSO, Unity Catalog governance)
   - Timeline (POC complete, ready for pilot)

### Emergency Recovery

If something breaks during demo:
- Switch to local: `http://localhost:5001`
- Show screenshots in `/screenshots/` folder
- Focus on the business value story, not the technology

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18.x + TypeScript, Material-UI 5.x, Recharts |
| Backend | Flask 3.x (Python) |
| Database | Delta Lake (Unity Catalog) |
| Deployment | Databricks Apps, Databricks Asset Bundles |
| SQL Warehouse | Databricks SQL Serverless |

## Project Structure

```
gpc-reliability-tracker/
├── app/                    # Flask backend
│   ├── __init__.py         # App factory
│   ├── config.py           # Configuration
│   ├── database.py         # Databricks SQL connector
│   ├── models/             # Data models
│   ├── routes/             # API blueprints
│   └── static/             # Built frontend assets
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks (React Query)
│   │   ├── services/       # API client
│   │   └── theme/          # MUI theme
│   └── package.json
├── scripts/                # Utility scripts
│   └── seed_batch.py       # Database seeding (batch mode)
├── sql/                    # SQL schema files
├── tests/                  # Test suites
│   └── e2e/                # Playwright E2E tests
├── databricks.yml          # DABs config
├── app.yml                 # Databricks App config
└── requirements.txt        # Python dependencies
```

## Quick Start

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or use .env file)
export DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
export DATABRICKS_TOKEN=your-token
export DATABRICKS_CATALOG=main
export DATABRICKS_SCHEMA=gpc_reliability

# Run development server
flask --app wsgi:app run --port 5001 --debug
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server (for hot reload)
npm run dev

# Build for production
npm run build

# Copy build to Flask static folder
cp -r dist/* ../app/static/
```

### Database Setup

```bash
# Create schema and tables (run via Databricks SQL or CLI)
# See sql/001_create_schema.sql and sql/002_create_tables.sql

# Seed sample data (fast batch mode)
python scripts/seed_batch.py
```

### Deploy to Databricks

```bash
# Configure Databricks CLI profile
databricks auth login --profile your-profile

# Deploy bundle
databricks bundle deploy --target dev

# Deploy app
databricks apps deploy gpc-reliability-api \
  --source-code-path /Workspace/Users/you/.bundle/gpc-reliability-tracker/dev/files \
  --profile your-profile
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABRICKS_SERVER_HOSTNAME` | Databricks workspace hostname |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse HTTP path |
| `DATABRICKS_TOKEN` | Personal access token (local dev only) |
| `DATABRICKS_CATALOG` | Unity Catalog name (default: main) |
| `DATABRICKS_SCHEMA` | Schema name (default: gpc_reliability) |
| `FLASK_ENV` | Environment (development/production) |
| `FLASK_SECRET_KEY` | Flask secret key |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/summary` | GET | Dashboard metrics |
| `/api/v1/dashboard/next-actions` | GET | Priority action items |
| `/api/v1/projects` | GET | List projects (with filters) |
| `/api/v1/projects/{id}` | GET | Project detail |
| `/api/v1/projects/{id}` | PATCH | Update project |
| `/api/v1/vendors` | GET | List vendors |
| `/api/v1/vendors/{id}` | GET | Vendor detail |
| `/api/v1/alerts` | GET | List alerts |
| `/api/v1/alerts/stats` | GET | Alert statistics |
| `/api/v1/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/api/v1/milestones/{id}/complete` | POST | Complete milestone |

## License

Proprietary - Georgia Power Company / Apex Systems
