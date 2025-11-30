# GPC Reliability Tracker

A web-based application that enables Georgia Power's Reliability team to track 700+ capital projects across 15 vendors, replacing the current spreadsheet-based workflow with automated visibility, proactive alerting, and vendor accountability metrics.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18.x + TypeScript, Material-UI 5.x, Recharts, gantt-task-react |
| Backend | Flask 3.x (Python), SQLAlchemy 2.x |
| Database | PostgreSQL 15.x (Databricks Lakebase) |
| Deployment | Databricks Apps, Databricks Asset Bundles |
| Jobs | Databricks Jobs (scheduled batch processing) |

## Project Structure

```
gpc-reliability-tracker/
├── app/                    # Flask backend
│   ├── __init__.py         # App factory
│   ├── config.py           # Configuration
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # API blueprints
│   ├── services/           # Business logic
│   └── utils/              # Helpers
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   ├── store/          # Zustand stores
│   │   ├── theme/          # MUI theme
│   │   └── types/          # TypeScript types
│   └── package.json
├── jobs/                   # Databricks Jobs
├── tests/                  # Test suites
├── databricks.yml          # DABs config
└── requirements.txt        # Python dependencies
```

## Quick Start

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
flask run --debug
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
FLASK_ENV=development
FLASK_SECRET_KEY=your-secret-key
```

## License

Proprietary - Georgia Power Company
