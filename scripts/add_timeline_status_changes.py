#!/usr/bin/env python3
"""Add STATUS_CHANGE audit logs to demonstrate multi-segment timeline feature.

This script adds realistic status transition history for 10-15 projects in advanced statuses
to demonstrate the timeline visualization feature.
"""
import json
import subprocess
import uuid
from datetime import datetime, timedelta

WAREHOUSE_ID = "e5ecfb6a56491fdb"
CATALOG = "main"
SCHEMA = "gpc_reliability"

# Status progression stages
STAGES = [
    'authorized',
    'assigned_to_vendor',
    'design_submitted',
    'qa_qc',
    'approved',
    'construction_ready'
]

# User pool for realistic audit logs
USERS = [
    ("lance.burton@gpc.com", "lance.burton"),
    ("project.manager@gpc.com", "project.manager"),
    ("qa.reviewer@gpc.com", "qa.reviewer"),
    ("engineering@gpc.com", "engineering"),
    ("construction@gpc.com", "construction"),
]


def execute_sql(statement: str) -> dict:
    """Execute SQL via Databricks CLI."""
    payload = {"warehouse_id": WAREHOUSE_ID, "statement": statement, "wait_timeout": "50s"}
    cmd = ["databricks", "api", "post", "/api/2.0/sql/statements", "-p", "apex", "--json", json.dumps(payload)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return {"status": {"state": "FAILED", "error": {"message": result.stderr}}}
    return json.loads(result.stdout)


def table_name(table: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{table}"


def get_projects_for_timeline() -> list[dict]:
    """Get 15 projects with advanced statuses for timeline demonstration."""
    sql = f"""
        SELECT id, work_order_number, status, authorized_date
        FROM {table_name('projects')}
        WHERE status IN ('qa_qc', 'approved', 'construction_ready')
        ORDER BY authorized_date DESC
        LIMIT 15
    """

    result = execute_sql(sql)
    if result.get("status", {}).get("state") != "SUCCEEDED":
        print(f"Failed to fetch projects: {result.get('status', {}).get('error', {}).get('message', 'Unknown error')}")
        return []

    # Parse result
    projects = []
    data_array = result.get("result", {}).get("data_array", [])
    for row in data_array:
        projects.append({
            "id": row[0],
            "work_order_number": row[1],
            "status": row[2],
            "authorized_date": row[3]
        })

    return projects


def add_status_change_history(projects: list[dict]) -> int:
    """Add STATUS_CHANGE audit logs for all projects in batch."""
    print(f"Adding STATUS_CHANGE history for {len(projects)} projects...")

    values = []
    total_transitions = 0

    for idx, project in enumerate(projects):
        project_id = project['id']
        work_order = project['work_order_number']
        current_status = project['status']
        auth_date_str = project['authorized_date']

        # Parse authorized date
        auth_date = datetime.strptime(auth_date_str, "%Y-%m-%d")

        # Find current status index
        current_index = STAGES.index(current_status)

        print(f"\n{work_order} ({current_status}): Adding {current_index} transitions")

        # Create status changes for each transition up to current status
        for i in range(current_index):
            old_status = STAGES[i]
            new_status = STAGES[i + 1]

            # Calculate transition date (10-14 days between transitions)
            days_offset = (i + 1) * 12  # 12 days between each transition
            transition_date = auth_date + timedelta(days=days_offset)

            # Rotate through users for variety
            user_email, user_id = USERS[(idx + i) % len(USERS)]

            # Generate audit log entry
            audit_id = str(uuid.uuid4())
            changes_json = json.dumps({"status": [old_status, new_status]})

            values.append(
                f"('{audit_id}', '{project_id}', 'STATUS_CHANGE', 'status', "
                f"'{old_status}', '{new_status}', '{changes_json}', "
                f"'{user_id}', '{user_email}', '{transition_date.strftime('%Y-%m-%d %H:%M:%S')}')"
            )

            print(f"  {old_status} → {new_status} @ {transition_date.date()} by {user_email}")
            total_transitions += 1

    # Insert in chunks of 50
    inserted = 0
    for i in range(0, len(values), 50):
        chunk = values[i:i+50]
        sql = f"""INSERT INTO {table_name('audit_logs')}
            (id, project_id, action, field_name, old_value, new_value, changes, user_id, user_email, created_at)
            VALUES {', '.join(chunk)}"""

        result = execute_sql(sql)
        if result.get("status", {}).get("state") == "SUCCEEDED":
            inserted += len(chunk)
            print(f"\nInserted chunk {i//50 + 1}: {len(chunk)} records")
        else:
            print(f"Failed chunk {i//50 + 1}: {result.get('status', {}).get('error', {}).get('message', 'Unknown error')}")

    print(f"\n{'='*80}")
    print(f"Total STATUS_CHANGE records added: {inserted}")
    print(f"{'='*80}")

    return inserted


def verify_data() -> dict:
    """Verify the added STATUS_CHANGE records."""
    print("\nVerifying STATUS_CHANGE records...")

    # Count total STATUS_CHANGE records
    count_sql = f"""
        SELECT COUNT(*) as count
        FROM {table_name('audit_logs')}
        WHERE action = 'STATUS_CHANGE'
    """
    result = execute_sql(count_sql)
    total_count = 0
    if result.get("status", {}).get("state") == "SUCCEEDED":
        total_count = int(result.get("result", {}).get("data_array", [[0]])[0][0])
        print(f"  Total STATUS_CHANGE records: {total_count}")

    # Get sample project with full history
    sample_sql = f"""
        SELECT
            p.work_order_number,
            p.status as current_status,
            al.old_value,
            al.new_value,
            al.created_at,
            al.user_email
        FROM {table_name('audit_logs')} al
        JOIN {table_name('projects')} p ON al.project_id = p.id
        WHERE al.action = 'STATUS_CHANGE'
        ORDER BY p.work_order_number, al.created_at
        LIMIT 10
    """
    result = execute_sql(sample_sql)
    sample_data = []
    if result.get("status", {}).get("state") == "SUCCEEDED":
        data_array = result.get("result", {}).get("data_array", [])
        for row in data_array:
            sample_data.append({
                "work_order": row[0],
                "current_status": row[1],
                "old_value": row[2],
                "new_value": row[3],
                "created_at": row[4],
                "user_email": row[5]
            })

    return {
        "total_count": total_count,
        "sample_data": sample_data
    }


def print_sample_history(verification: dict):
    """Print a sample project's full status history."""
    print("\n" + "="*80)
    print("SAMPLE PROJECT STATUS HISTORY")
    print("="*80)

    sample_data = verification.get("sample_data", [])
    if not sample_data:
        print("No sample data available")
        return

    current_wo = None
    for entry in sample_data:
        wo = entry['work_order']
        if wo != current_wo:
            if current_wo is not None:
                print()  # Separator between projects
            print(f"\n{wo} (Current: {entry['current_status']})")
            print("-" * 80)
            current_wo = wo

        print(f"  {entry['old_value']:20s} → {entry['new_value']:20s} | {entry['created_at']} | {entry['user_email']}")


def main():
    print("="*80)
    print("Adding STATUS_CHANGE Audit Logs for Multi-Segment Timeline Demo")
    print("="*80)

    # Step 1: Get projects
    projects = get_projects_for_timeline()
    if not projects:
        print("No projects found!")
        return

    print(f"\nFound {len(projects)} projects in advanced statuses:")
    status_counts = {}
    for p in projects:
        status = p['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    # Step 2: Add status change history
    inserted = add_status_change_history(projects)

    # Step 3: Verify data
    verification = verify_data()

    # Step 4: Print sample history
    print_sample_history(verification)

    # Step 5: Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Projects updated: {len(projects)}")
    print(f"STATUS_CHANGE records added: {inserted}")
    print(f"Total STATUS_CHANGE records in DB: {verification['total_count']}")

    print("\n" + "="*80)
    print("VERIFICATION INSTRUCTIONS")
    print("="*80)
    print("To verify the data, run the following queries in Databricks SQL Editor:")
    print()
    print("1. Count STATUS_CHANGE records:")
    print("   SELECT COUNT(*) FROM main.gpc_reliability.audit_logs WHERE action='STATUS_CHANGE';")
    print()
    print("2. View status history for a project:")
    print("   SELECT p.work_order_number, al.old_value, al.new_value, al.created_at")
    print("   FROM main.gpc_reliability.audit_logs al")
    print("   JOIN main.gpc_reliability.projects p ON al.project_id = p.id")
    print("   WHERE al.action='STATUS_CHANGE'")
    print("   ORDER BY p.work_order_number, al.created_at;")
    print()
    print("3. Test the API endpoint:")
    print("   curl http://127.0.0.1:5001/api/v1/gantt?work_order=WO-20240637")
    print()
    print("="*80)


if __name__ == "__main__":
    main()
