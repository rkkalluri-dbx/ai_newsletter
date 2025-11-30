# Database Setup Guide

## Delta Lake + Unity Catalog

This application uses Delta Lake tables in Unity Catalog with Databricks SQL Warehouse for data persistence.

### Prerequisites

1. Access to Databricks workspace with Unity Catalog enabled
2. SQL Warehouse (Serverless or Classic)
3. Permissions to create schemas and tables in Unity Catalog
4. Databricks CLI configured

### Architecture

```
Unity Catalog
└── main (catalog)
    └── gpc_reliability (schema)
        ├── vendors
        ├── projects
        ├── milestones
        ├── alerts
        ├── audit_logs
        └── vendor_metrics
```

### Creating the Schema and Tables

#### Option 1: Via Databricks SQL Editor (Recommended)

1. Navigate to **SQL Editor** in Databricks
2. Run the SQL scripts in order:

```sql
-- Run sql/001_create_schema.sql first
CREATE SCHEMA IF NOT EXISTS main.gpc_reliability
COMMENT 'GPC Reliability Project Workflow Tracker';

-- Then run sql/002_create_tables.sql
-- (See file for full CREATE TABLE statements)
```

#### Option 2: Via Flask CLI

```bash
# Set environment variables first
export DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
export DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
export DATABRICKS_TOKEN=your-token

# Initialize database
flask init-db
```

### Environment Variables

Set these in your environment or `.env` file:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_APP=wsgi:app
FLASK_SECRET_KEY=your-secret-key

# Databricks Unity Catalog Configuration
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=your-personal-access-token
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=gpc_reliability
```

### Finding Your SQL Warehouse HTTP Path

1. Go to **SQL Warehouses** in Databricks
2. Click on your warehouse
3. Go to **Connection details** tab
4. Copy the **HTTP path** (e.g., `/sql/1.0/warehouses/abc123def456`)

### Databricks Apps Authentication

When running in Databricks Apps, authentication is handled automatically via the app's service principal. You don't need to set `DATABRICKS_TOKEN` - the connector will use the default authentication.

### Seeding Data

```bash
# Seed all tables with mock data
flask db-seed all

# Seed only vendors
flask db-seed vendors

# Clear all data (with confirmation)
flask db-seed clear
```

### Checking Database Connection

```bash
# Verify connection and list tables
flask check-db
```

### Delta Lake Features

Delta Lake provides:

- **ACID Transactions**: All operations are atomic
- **Schema Enforcement**: Columns and types are validated
- **Time Travel**: Query historical versions of data
- **Optimized Performance**: Auto-optimization with Z-ordering

### Querying Data Directly

You can query the tables directly in Databricks SQL:

```sql
-- List all projects
SELECT * FROM main.gpc_reliability.projects;

-- Find overdue milestones
SELECT m.*, p.work_order_number
FROM main.gpc_reliability.milestones m
JOIN main.gpc_reliability.projects p ON m.project_id = p.id
WHERE m.is_overdue = true;

-- Vendor performance summary
SELECT v.name, vm.*
FROM main.gpc_reliability.vendor_metrics vm
JOIN main.gpc_reliability.vendors v ON vm.vendor_id = v.id
ORDER BY vm.on_time_rate DESC;
```

### Troubleshooting

#### Connection Issues

```bash
# Test connection
databricks sql execute --http-path /sql/1.0/warehouses/your-id \
  --statement "SELECT 1"
```

#### Permission Errors

Ensure your user/service principal has:
- `USE CATALOG` on the catalog
- `USE SCHEMA` on the schema
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tables

```sql
-- Grant permissions (run as admin)
GRANT USE CATALOG ON CATALOG main TO `user@example.com`;
GRANT USE SCHEMA ON SCHEMA main.gpc_reliability TO `user@example.com`;
GRANT ALL PRIVILEGES ON SCHEMA main.gpc_reliability TO `user@example.com`;
```
