-- Create Delta tables for GPC Reliability Tracker
-- Run this in Databricks SQL Editor or via CLI

USE main.gpc_reliability;

-- Vendors table
CREATE TABLE IF NOT EXISTS vendors (
    id STRING NOT NULL,
    name STRING NOT NULL,
    code STRING NOT NULL,
    contact_name STRING,
    contact_email STRING,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'External contractors/vendors';

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id STRING NOT NULL,
    work_order_number STRING NOT NULL,
    vendor_id STRING NOT NULL,
    description STRING,
    region STRING,
    status STRING NOT NULL,
    priority STRING NOT NULL,
    authorized_date DATE,
    sent_to_vendor_date DATE,
    received_from_vendor_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    revision_count INT NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Capital projects tracked through workflow';

-- Milestones table
CREATE TABLE IF NOT EXISTS milestones (
    id STRING NOT NULL,
    project_id STRING NOT NULL,
    stage STRING NOT NULL,
    expected_date DATE,
    actual_date DATE,
    sla_days INT,
    is_overdue BOOLEAN NOT NULL,
    days_overdue INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Project milestone checkpoints';

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id STRING NOT NULL,
    project_id STRING NOT NULL,
    alert_type STRING NOT NULL,
    message STRING NOT NULL,
    severity STRING NOT NULL,
    is_acknowledged BOOLEAN NOT NULL,
    acknowledged_at TIMESTAMP,
    acknowledged_by STRING,
    created_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Project alerts and notifications';

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id STRING NOT NULL,
    project_id STRING NOT NULL,
    action STRING NOT NULL,
    field_name STRING,
    old_value STRING,
    new_value STRING,
    changes STRING,  -- JSON string for multiple field changes
    user_id STRING,
    user_email STRING,
    created_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Project change audit trail';

-- Vendor metrics table
CREATE TABLE IF NOT EXISTS vendor_metrics (
    id STRING NOT NULL,
    vendor_id STRING NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_projects INT NOT NULL,
    completed_projects INT NOT NULL,
    active_projects INT NOT NULL,
    overdue_projects INT NOT NULL,
    on_time_rate DOUBLE NOT NULL,
    avg_cycle_time_days DOUBLE,
    revision_rate DOUBLE NOT NULL,
    sla_compliance_rate DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
USING DELTA
COMMENT 'Vendor performance metrics by period';
