#!/usr/bin/env python3
"""Seed Delta tables via Databricks CLI using batch inserts."""
import json
import random
import subprocess
import uuid
from datetime import date, datetime, timedelta

WAREHOUSE_ID = "e5ecfb6a56491fdb"
CATALOG = "main"
SCHEMA = "gpc_reliability"

VENDOR_DATA = [
    ("Pike Electric Corporation", "PIKE", "John Smith", "jsmith@pikeelectric.com"),
    ("MYR Group Inc.", "MYR", "Sarah Johnson", "sjohnson@myrgroup.com"),
    ("Quanta Services", "QUANTA", "Mike Davis", "mdavis@quantaservices.com"),
    ("Mastec Inc.", "MASTEC", "Lisa Brown", "lbrown@mastec.com"),
    ("Dycom Industries", "DYCOM", "Robert Wilson", "rwilson@dycom.com"),
    ("Black and Veatch", "BV", "Jennifer Lee", "jlee@bv.com"),
    ("Primoris Services", "PRIMO", "David Martinez", "dmartinez@primoris.com"),
    ("Willbros Group", "WILL", "Amanda Taylor", "ataylor@willbros.com"),
    ("Infrastructure Energy Alt", "IEA", "Chris Anderson", "canderson@iea.net"),
    ("PAR Electrical Contractors", "PAR", "Michelle Thomas", "mthomas@parelectric.com"),
    ("Summit Line Construction", "SUMMIT", "James Jackson", "jjackson@summitline.com"),
    ("Henkels and McCoy Group", "HMG", "Patricia White", "pwhite@henkels.com"),
    ("Asplundh Tree Expert", "ASPLUNDH", "Richard Harris", "rharris@asplundh.com"),
    ("EMCOR Group", "EMCOR", "Susan Clark", "sclark@emcor.net"),
    ("Michels Corporation", "MICHELS", "Daniel Lewis", "dlewis@michels.us"),
]

REGIONS = ["Metro Atlanta", "North Georgia", "Central Georgia", "South Georgia",
           "Coastal Georgia", "West Georgia", "East Georgia", "Augusta Area"]
STATUSES = ["authorized", "assigned_to_vendor", "design_submitted", "qa_qc", "approved", "construction_ready"]
PRIORITIES = ["low", "normal", "high", "critical"]


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


def seed_vendors() -> list[str]:
    """Seed all vendors in a single batch insert."""
    print("Seeding vendors...")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    vendor_ids = [str(uuid.uuid4()) for _ in VENDOR_DATA]

    values = []
    for vid, (name, code, contact, email) in zip(vendor_ids, VENDOR_DATA):
        values.append(f"('{vid}', '{name}', '{code}', '{contact}', '{email}', true, '{now}', '{now}')")

    sql = f"""INSERT INTO {table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES {', '.join(values)}"""

    result = execute_sql(sql)
    if result.get("status", {}).get("state") == "SUCCEEDED":
        print(f"  ✓ Seeded {len(vendor_ids)} vendors")
    else:
        print(f"  ✗ Failed: {result.get('status', {}).get('error', {}).get('message', 'Unknown error')}")
    return vendor_ids


def seed_projects(vendor_ids: list[str], count: int = 50) -> list[str]:
    """Seed projects in batch."""
    print("Seeding projects...")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    project_ids = []
    values = []

    for i in range(count):
        pid = str(uuid.uuid4())
        project_ids.append(pid)
        vendor_id = random.choice(vendor_ids)
        region = random.choice(REGIONS)
        status = random.choice(STATUSES)
        priority = random.choice(PRIORITIES)
        auth_date = date.today() - timedelta(days=random.randint(30, 180))
        status_idx = STATUSES.index(status)

        sent = f"'{auth_date + timedelta(days=random.randint(1, 7))}'" if status_idx >= 1 else "NULL"
        recv = f"'{auth_date + timedelta(days=random.randint(10, 40))}'" if status_idx >= 2 else "NULL"
        target = f"'{auth_date + timedelta(days=random.randint(60, 120))}'" if status_idx >= 5 else "NULL"
        actual = f"'{auth_date + timedelta(days=random.randint(70, 140))}'" if status_idx >= 5 and random.random() > 0.3 else "NULL"

        desc = f"{region} infrastructure project {i+1}"
        values.append(f"('{pid}', 'WO-2024{i+1:04d}', '{vendor_id}', '{desc}', '{region}', "
                     f"'{status}', '{priority}', '{auth_date}', {sent}, {recv}, {target}, {actual}, "
                     f"{random.randint(0, 5)}, 1, '{now}', '{now}')")

    sql = f"""INSERT INTO {table_name('projects')}
        (id, work_order_number, vendor_id, description, region, status, priority,
         authorized_date, sent_to_vendor_date, received_from_vendor_date,
         target_completion_date, actual_completion_date, revision_count, version,
         created_at, updated_at)
        VALUES {', '.join(values)}"""

    result = execute_sql(sql)
    if result.get("status", {}).get("state") == "SUCCEEDED":
        print(f"  ✓ Seeded {len(project_ids)} projects")
    else:
        print(f"  ✗ Failed: {result.get('status', {}).get('error', {}).get('message', 'Unknown error')}")
    return project_ids


def seed_milestones(project_ids: list[str]) -> int:
    """Seed milestones in batches."""
    print("Seeding milestones...")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    sla_map = {"authorized": "NULL", "assigned_to_vendor": "7", "design_submitted": "NULL",
               "qa_qc": "7", "approved": "3", "construction_ready": "NULL"}
    values = []

    for pid in project_ids:
        base_date = date.today() - timedelta(days=random.randint(30, 90))
        status_idx = random.randint(0, 5)

        for i, stage in enumerate(STATUSES):
            mid = str(uuid.uuid4())
            exp_date = base_date + timedelta(days=i * 14)
            actual = f"'{exp_date + timedelta(days=random.randint(-3, 5))}'" if i <= status_idx else "NULL"
            is_overdue = "true" if actual == "NULL" and exp_date < date.today() else "false"
            days_overdue = (date.today() - exp_date).days if is_overdue == "true" else 0

            values.append(f"('{mid}', '{pid}', '{stage}', '{exp_date}', {actual}, "
                         f"{sla_map[stage]}, {is_overdue}, {days_overdue}, '{now}', '{now}')")

    # Insert in chunks of 100
    total = 0
    for i in range(0, len(values), 100):
        chunk = values[i:i+100]
        sql = f"""INSERT INTO {table_name('milestones')}
            (id, project_id, stage, expected_date, actual_date, sla_days,
             is_overdue, days_overdue, created_at, updated_at)
            VALUES {', '.join(chunk)}"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") == "SUCCEEDED":
            total += len(chunk)

    print(f"  ✓ Seeded {total} milestones")
    return total


def seed_alerts(project_ids: list[str]) -> int:
    """Seed alerts in batch."""
    print("Seeding alerts...")
    values = []

    for pid in project_ids:
        if random.random() > 0.7:
            for _ in range(random.randint(1, 3)):
                aid = str(uuid.uuid4())
                alert_type = random.choice(["milestone_overdue", "milestone_approaching", "status_change"])
                severity = random.choice(["info", "warning", "critical"])
                is_ack = random.random() > 0.5
                created = (datetime.utcnow() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
                ack_at = f"'{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}'" if is_ack else "NULL"
                ack_by = "'system@gpc.com'" if is_ack else "NULL"

                values.append(f"('{aid}', '{pid}', '{alert_type}', 'Alert for project', '{severity}', "
                             f"{str(is_ack).lower()}, {ack_at}, {ack_by}, '{created}')")

    if values:
        sql = f"""INSERT INTO {table_name('alerts')}
            (id, project_id, alert_type, message, severity, is_acknowledged,
             acknowledged_at, acknowledged_by, created_at)
            VALUES {', '.join(values)}"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") == "SUCCEEDED":
            print(f"  ✓ Seeded {len(values)} alerts")
            return len(values)

    print(f"  ✓ Seeded {len(values)} alerts")
    return len(values)


def seed_audit_logs(project_ids: list[str]) -> int:
    """Seed audit logs in batch."""
    print("Seeding audit logs...")
    values = []
    actions = ["create", "update", "status_change"]

    for pid in project_ids:
        for i in range(random.randint(2, 4)):
            lid = str(uuid.uuid4())
            action = random.choice(actions)
            created = (datetime.utcnow() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S")
            user = f"user{random.randint(1, 10)}@gpc.com"

            field = "'status'" if action == "status_change" else "NULL"
            old_val = f"'{STATUSES[max(0, i-1)]}'" if action == "status_change" else "NULL"
            new_val = f"'{STATUSES[min(i, 5)]}'" if action == "status_change" else "NULL"

            values.append(f"('{lid}', '{pid}', '{action}', {field}, {old_val}, {new_val}, "
                         f"NULL, '{user}', '{user}', '{created}')")

    # Insert in chunks
    total = 0
    for i in range(0, len(values), 100):
        chunk = values[i:i+100]
        sql = f"""INSERT INTO {table_name('audit_logs')}
            (id, project_id, action, field_name, old_value, new_value, changes,
             user_id, user_email, created_at)
            VALUES {', '.join(chunk)}"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") == "SUCCEEDED":
            total += len(chunk)

    print(f"  ✓ Seeded {total} audit logs")
    return total


def seed_vendor_metrics(vendor_ids: list[str]) -> int:
    """Seed vendor metrics in batch."""
    print("Seeding vendor metrics...")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    period_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    period_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    values = []

    for vid in vendor_ids:
        mid = str(uuid.uuid4())
        total = random.randint(20, 80)
        completed = random.randint(10, total - 5)
        active = total - completed
        overdue = random.randint(0, min(10, active))

        values.append(f"('{mid}', '{vid}', '{period_start}', '{period_end}', {total}, {completed}, "
                     f"{active}, {overdue}, {round(random.uniform(70, 98), 2)}, "
                     f"{round(random.uniform(30, 90), 1)}, {round(random.uniform(0.5, 2.5), 2)}, "
                     f"{round(random.uniform(75, 99), 2)}, '{now}', '{now}')")

    sql = f"""INSERT INTO {table_name('vendor_metrics')}
        (id, vendor_id, period_start, period_end, total_projects, completed_projects,
         active_projects, overdue_projects, on_time_rate, avg_cycle_time_days,
         revision_rate, sla_compliance_rate, created_at, updated_at)
        VALUES {', '.join(values)}"""

    result = execute_sql(sql)
    if result.get("status", {}).get("state") == "SUCCEEDED":
        print(f"  ✓ Seeded {len(values)} vendor metrics")
    return len(values)


def main():
    print("=" * 50)
    print("Seeding GPC Reliability Database (Batch Mode)")
    print("=" * 50)

    vendor_ids = seed_vendors()
    project_ids = seed_projects(vendor_ids, count=50)
    seed_milestones(project_ids)
    seed_alerts(project_ids)
    seed_audit_logs(project_ids)
    seed_vendor_metrics(vendor_ids)

    print("=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
