#!/usr/bin/env python3
"""Seed Delta tables via Databricks CLI."""
import json
import random
import subprocess
import uuid
from datetime import date, datetime, timedelta

WAREHOUSE_ID = "84823cd491f18a44"
CATALOG = "main"
SCHEMA = "gpc_reliability"

# Mock vendor data - 15 vendors
VENDOR_DATA = [
    {"name": "Pike Electric Corporation", "code": "PIKE", "contact_name": "John Smith", "contact_email": "jsmith@pikeelectric.com"},
    {"name": "MYR Group Inc.", "code": "MYR", "contact_name": "Sarah Johnson", "contact_email": "sjohnson@myrgroup.com"},
    {"name": "Quanta Services", "code": "QUANTA", "contact_name": "Mike Davis", "contact_email": "mdavis@quantaservices.com"},
    {"name": "Mastec Inc.", "code": "MASTEC", "contact_name": "Lisa Brown", "contact_email": "lbrown@mastec.com"},
    {"name": "Dycom Industries", "code": "DYCOM", "contact_name": "Robert Wilson", "contact_email": "rwilson@dycom.com"},
    {"name": "Black and Veatch", "code": "BV", "contact_name": "Jennifer Lee", "contact_email": "jlee@bv.com"},
    {"name": "Primoris Services", "code": "PRIMO", "contact_name": "David Martinez", "contact_email": "dmartinez@primoris.com"},
    {"name": "Willbros Group", "code": "WILL", "contact_name": "Amanda Taylor", "contact_email": "ataylor@willbros.com"},
    {"name": "Infrastructure and Energy Alternatives", "code": "IEA", "contact_name": "Chris Anderson", "contact_email": "canderson@iea.net"},
    {"name": "PAR Electrical Contractors", "code": "PAR", "contact_name": "Michelle Thomas", "contact_email": "mthomas@parelectric.com"},
    {"name": "Summit Line Construction", "code": "SUMMIT", "contact_name": "James Jackson", "contact_email": "jjackson@summitline.com"},
    {"name": "Henkels and McCoy Group", "code": "HMG", "contact_name": "Patricia White", "contact_email": "pwhite@henkels.com"},
    {"name": "Asplundh Tree Expert", "code": "ASPLUNDH", "contact_name": "Richard Harris", "contact_email": "rharris@asplundh.com"},
    {"name": "EMCOR Group", "code": "EMCOR", "contact_name": "Susan Clark", "contact_email": "sclark@emcor.net"},
    {"name": "Michels Corporation", "code": "MICHELS", "contact_name": "Daniel Lewis", "contact_email": "dlewis@michels.us"},
]

REGIONS = ["Metro Atlanta", "North Georgia", "Central Georgia", "South Georgia",
           "Coastal Georgia", "West Georgia", "East Georgia", "Augusta Area"]

PROJECT_DESCRIPTIONS = [
    "Pole replacement and line upgrade for {} distribution circuit",
    "Underground cable installation in {} residential area",
    "Substation upgrade project - {} 115kV expansion",
    "Storm damage repair - {} feeder restoration",
    "New service extension for commercial development in {}",
]

STATUSES = ["authorized", "assigned_to_vendor", "design_submitted", "qa_qc", "approved", "construction_ready"]
PRIORITIES = ["low", "normal", "high", "critical"]
STAGES = ["authorized", "assigned_to_vendor", "design_submitted", "qa_qc", "approved", "construction_ready"]
ALERT_TYPES = ["milestone_overdue", "milestone_approaching", "status_change", "revision_added"]
SEVERITIES = ["info", "warning", "critical"]
ACTIONS = ["create", "update", "delete", "status_change", "revision_added"]


def execute_sql(statement: str) -> dict:
    """Execute SQL via Databricks CLI."""
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": statement,
        "wait_timeout": "30s"
    }
    cmd = ["databricks", "api", "post", "/api/2.0/sql/statements", "-p", "DEFAULT", "--json", json.dumps(payload)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return {"status": {"state": "FAILED"}}
    return json.loads(result.stdout)


def table_name(table: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{table}"


def seed_vendors() -> list[str]:
    """Seed vendors and return list of IDs."""
    print("Seeding vendors...")
    vendor_ids = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    for data in VENDOR_DATA:
        vid = str(uuid.uuid4())
        vendor_ids.append(vid)
        sql = f"""INSERT INTO {table_name('vendors')}
            (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
            VALUES ('{vid}', '{data["name"]}', '{data["code"]}', '{data["contact_name"]}',
                    '{data["contact_email"]}', true, '{now}', '{now}')"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") != "SUCCEEDED":
            print(f"  Failed to insert vendor {data['code']}")

    print(f"  Seeded {len(vendor_ids)} vendors")
    return vendor_ids


def seed_projects(vendor_ids: list[str], count: int = 50) -> list[str]:
    """Seed projects and return list of IDs."""
    print("Seeding projects...")
    project_ids = []
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    for i in range(count):
        pid = str(uuid.uuid4())
        project_ids.append(pid)

        vendor_id = random.choice(vendor_ids)
        region = random.choice(REGIONS)
        status = random.choice(STATUSES)
        priority = random.choice(PRIORITIES)

        auth_date = date.today() - timedelta(days=random.randint(30, 180))
        status_idx = STATUSES.index(status)

        sent_date = "NULL"
        recv_date = "NULL"
        target_date = "NULL"
        actual_date = "NULL"

        if status_idx >= 1:
            sent_date = f"'{auth_date + timedelta(days=random.randint(1, 7))}'"
        if status_idx >= 2:
            recv_date = f"'{auth_date + timedelta(days=random.randint(10, 40))}'"
        if status_idx >= 5:
            target_date = f"'{auth_date + timedelta(days=random.randint(60, 120))}'"
            if random.random() > 0.3:
                actual_date = f"'{auth_date + timedelta(days=random.randint(70, 140))}'"

        desc = random.choice(PROJECT_DESCRIPTIONS).format(region)

        sql = f"""INSERT INTO {table_name('projects')}
            (id, work_order_number, vendor_id, description, region, status, priority,
             authorized_date, sent_to_vendor_date, received_from_vendor_date,
             target_completion_date, actual_completion_date, revision_count, version,
             created_at, updated_at)
            VALUES ('{pid}', 'WO-2024{i+1:04d}', '{vendor_id}', '{desc}', '{region}',
                    '{status}', '{priority}', '{auth_date}', {sent_date}, {recv_date},
                    {target_date}, {actual_date}, {random.randint(0, 5)}, 1, '{now}', '{now}')"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") != "SUCCEEDED":
            print(f"  Failed to insert project WO-2024{i+1:04d}")

    print(f"  Seeded {len(project_ids)} projects")
    return project_ids


def seed_milestones(project_ids: list[str]) -> int:
    """Seed milestones for each project."""
    print("Seeding milestones...")
    count = 0
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    sla_map = {"authorized": "NULL", "assigned_to_vendor": "7", "design_submitted": "NULL",
               "qa_qc": "7", "approved": "3", "construction_ready": "NULL"}

    for pid in project_ids:
        base_date = date.today() - timedelta(days=random.randint(30, 90))
        status_idx = random.randint(0, 5)

        for i, stage in enumerate(STAGES):
            mid = str(uuid.uuid4())
            exp_date = base_date + timedelta(days=i * 14)
            actual = "NULL"
            is_overdue = "false"
            days_overdue = 0

            if i <= status_idx:
                actual = f"'{exp_date + timedelta(days=random.randint(-3, 5))}'"
            elif exp_date < date.today():
                is_overdue = "true"
                days_overdue = (date.today() - exp_date).days

            sql = f"""INSERT INTO {table_name('milestones')}
                (id, project_id, stage, expected_date, actual_date, sla_days,
                 is_overdue, days_overdue, created_at, updated_at)
                VALUES ('{mid}', '{pid}', '{stage}', '{exp_date}', {actual},
                        {sla_map[stage]}, {is_overdue}, {days_overdue}, '{now}', '{now}')"""
            result = execute_sql(sql)
            if result.get("status", {}).get("state") == "SUCCEEDED":
                count += 1

    print(f"  Seeded {count} milestones")
    return count


def seed_alerts(project_ids: list[str]) -> int:
    """Seed alerts for some projects."""
    print("Seeding alerts...")
    count = 0

    for pid in project_ids:
        if random.random() > 0.7:
            for _ in range(random.randint(1, 3)):
                aid = str(uuid.uuid4())
                alert_type = random.choice(ALERT_TYPES)
                severity = random.choice(SEVERITIES)
                is_ack = random.random() > 0.5
                created = (datetime.utcnow() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")

                msg = f"{alert_type.replace('_', ' ').title()} for project"
                ack_at = f"'{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}'" if is_ack else "NULL"
                ack_by = "'system@gpc.com'" if is_ack else "NULL"

                sql = f"""INSERT INTO {table_name('alerts')}
                    (id, project_id, alert_type, message, severity, is_acknowledged,
                     acknowledged_at, acknowledged_by, created_at)
                    VALUES ('{aid}', '{pid}', '{alert_type}', '{msg}', '{severity}',
                            {str(is_ack).lower()}, {ack_at}, {ack_by}, '{created}')"""
                result = execute_sql(sql)
                if result.get("status", {}).get("state") == "SUCCEEDED":
                    count += 1

    print(f"  Seeded {count} alerts")
    return count


def seed_audit_logs(project_ids: list[str]) -> int:
    """Seed audit logs for projects."""
    print("Seeding audit logs...")
    count = 0

    for pid in project_ids:
        for i in range(random.randint(2, 4)):
            lid = str(uuid.uuid4())
            action = random.choice(ACTIONS)
            created = (datetime.utcnow() - timedelta(days=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S")
            user = f"user{random.randint(1, 10)}@gpc.com"

            field = "'status'" if action == "status_change" else "NULL"
            old_val = f"'{STATUSES[max(0, i-1)]}'" if action == "status_change" else "NULL"
            new_val = f"'{STATUSES[min(i, 5)]}'" if action == "status_change" else "NULL"

            sql = f"""INSERT INTO {table_name('audit_logs')}
                (id, project_id, action, field_name, old_value, new_value, changes,
                 user_id, user_email, created_at)
                VALUES ('{lid}', '{pid}', '{action}', {field}, {old_val}, {new_val},
                        NULL, '{user}', '{user}', '{created}')"""
            result = execute_sql(sql)
            if result.get("status", {}).get("state") == "SUCCEEDED":
                count += 1

    print(f"  Seeded {count} audit logs")
    return count


def seed_vendor_metrics(vendor_ids: list[str]) -> int:
    """Seed vendor metrics."""
    print("Seeding vendor metrics...")
    count = 0
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    period_end = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    period_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    for vid in vendor_ids:
        mid = str(uuid.uuid4())
        total = random.randint(20, 80)
        completed = random.randint(10, total - 5)
        active = total - completed
        overdue = random.randint(0, min(10, active))

        sql = f"""INSERT INTO {table_name('vendor_metrics')}
            (id, vendor_id, period_start, period_end, total_projects, completed_projects,
             active_projects, overdue_projects, on_time_rate, avg_cycle_time_days,
             revision_rate, sla_compliance_rate, created_at, updated_at)
            VALUES ('{mid}', '{vid}', '{period_start}', '{period_end}', {total}, {completed},
                    {active}, {overdue}, {round(random.uniform(70, 98), 2)},
                    {round(random.uniform(30, 90), 1)}, {round(random.uniform(0.5, 2.5), 2)},
                    {round(random.uniform(75, 99), 2)}, '{now}', '{now}')"""
        result = execute_sql(sql)
        if result.get("status", {}).get("state") == "SUCCEEDED":
            count += 1

    print(f"  Seeded {count} vendor metrics")
    return count


def main():
    print("=" * 50)
    print("Seeding GPC Reliability Database")
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
