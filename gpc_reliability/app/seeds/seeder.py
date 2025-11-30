"""Database seeder for mock data using Delta Lake."""
import random
import uuid
from datetime import date, datetime, timedelta

from app.database import db
from app.models.project import ProjectStatus, Priority
from app.models.milestone import MilestoneStage
from app.models.alert import AlertType, AlertSeverity
from app.models.audit_log import AuditAction


# Mock vendor data - 15 active vendors
VENDOR_DATA = [
    {"name": "Pike Electric Corporation", "code": "PIKE", "contact_name": "John Smith", "contact_email": "jsmith@pikeelectric.com"},
    {"name": "MYR Group Inc.", "code": "MYR", "contact_name": "Sarah Johnson", "contact_email": "sjohnson@myrgroup.com"},
    {"name": "Quanta Services", "code": "QUANTA", "contact_name": "Mike Davis", "contact_email": "mdavis@quantaservices.com"},
    {"name": "Mastec Inc.", "code": "MASTEC", "contact_name": "Lisa Brown", "contact_email": "lbrown@mastec.com"},
    {"name": "Dycom Industries", "code": "DYCOM", "contact_name": "Robert Wilson", "contact_email": "rwilson@dycom.com"},
    {"name": "Black & Veatch", "code": "BV", "contact_name": "Jennifer Lee", "contact_email": "jlee@bv.com"},
    {"name": "Primoris Services", "code": "PRIMO", "contact_name": "David Martinez", "contact_email": "dmartinez@primoris.com"},
    {"name": "Willbros Group", "code": "WILL", "contact_name": "Amanda Taylor", "contact_email": "ataylor@willbros.com"},
    {"name": "Infrastructure & Energy Alternatives", "code": "IEA", "contact_name": "Chris Anderson", "contact_email": "canderson@iea.net"},
    {"name": "PAR Electrical Contractors", "code": "PAR", "contact_name": "Michelle Thomas", "contact_email": "mthomas@parelectric.com"},
    {"name": "Summit Line Construction", "code": "SUMMIT", "contact_name": "James Jackson", "contact_email": "jjackson@summitline.com"},
    {"name": "Henkels & McCoy Group", "code": "HMG", "contact_name": "Patricia White", "contact_email": "pwhite@henkels.com"},
    {"name": "Asplundh Tree Expert", "code": "ASPLUNDH", "contact_name": "Richard Harris", "contact_email": "rharris@asplundh.com"},
    {"name": "EMCOR Group", "code": "EMCOR", "contact_name": "Susan Clark", "contact_email": "sclark@emcor.net"},
    {"name": "Michels Corporation", "code": "MICHELS", "contact_name": "Daniel Lewis", "contact_email": "dlewis@michels.us"},
]

# Inactive vendor data - 5 vendors (contract ended, performance issues, etc.)
INACTIVE_VENDOR_DATA = [
    {"name": "Legacy Power Solutions", "code": "LEGACY", "contact_name": "Tom Bradley", "contact_email": "tbradley@legacypower.com"},
    {"name": "Southern Grid Services", "code": "SGS", "contact_name": "Karen Mitchell", "contact_email": "kmitchell@southerngrid.com"},
    {"name": "Atlantic Electric Works", "code": "AEW", "contact_name": "Frank Rodriguez", "contact_email": "frodriguez@atlanticelectric.com"},
    {"name": "Peachtree Utility Contractors", "code": "PUC", "contact_name": "Nancy Cooper", "contact_email": "ncooper@peachtreeutility.com"},
    {"name": "Dixie Line Construction", "code": "DIXIE", "contact_name": "Bill Thompson", "contact_email": "bthompson@dixieline.com"},
]

# Georgia regions
REGIONS = [
    "Metro Atlanta", "North Georgia", "Central Georgia", "South Georgia",
    "Coastal Georgia", "West Georgia", "East Georgia", "Augusta Area"
]

# Project description templates
PROJECT_DESCRIPTIONS = [
    "Pole replacement and line upgrade for {region} distribution circuit",
    "Underground cable installation in {region} residential area",
    "Substation upgrade project - {region} 115kV expansion",
    "Storm damage repair - {region} feeder restoration",
    "New service extension for commercial development in {region}",
    "Vegetation management and line clearance - {region}",
    "Transformer upgrade program - {region} industrial district",
    "Smart grid infrastructure deployment - {region}",
    "Reliability improvement project - {region} loop tie",
    "Emergency repair and reinforcement - {region}",
]


def seed_vendors() -> list[str]:
    """Seed vendor records (active and inactive). Returns list of active vendor IDs."""
    vendor_ids = []
    now = datetime.utcnow().isoformat()

    # Seed active vendors
    for data in VENDOR_DATA:
        vendor_id = str(uuid.uuid4())
        vendor_ids.append(vendor_id)

        query = f"""
        INSERT INTO {db.table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES ('{vendor_id}', '{data["name"]}', '{data["code"]}',
                '{data["contact_name"]}', '{data["contact_email"]}', true,
                '{now}', '{now}')
        """
        db.execute_write(query)

    # Seed inactive vendors
    for data in INACTIVE_VENDOR_DATA:
        vendor_id = str(uuid.uuid4())
        # Don't add inactive vendor IDs to the return list (they won't get projects assigned)

        query = f"""
        INSERT INTO {db.table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES ('{vendor_id}', '{data["name"]}', '{data["code"]}',
                '{data["contact_name"]}', '{data["contact_email"]}', false,
                '{now}', '{now}')
        """
        db.execute_write(query)

    print(f"Seeded {len(VENDOR_DATA)} active vendors and {len(INACTIVE_VENDOR_DATA)} inactive vendors")
    return vendor_ids


def seed_projects(vendor_ids: list[str], count: int = 50) -> list[str]:
    """Seed project records. Returns list of project IDs."""
    project_ids = []
    statuses = ProjectStatus.ALL
    priorities = Priority.ALL
    now = datetime.utcnow().isoformat()

    for i in range(count):
        project_id = str(uuid.uuid4())
        project_ids.append(project_id)

        vendor_id = random.choice(vendor_ids)
        region = random.choice(REGIONS)
        status = random.choice(statuses)
        priority = random.choice(priorities)

        # Generate dates based on status
        authorized_date = date.today() - timedelta(days=random.randint(30, 180))
        sent_to_vendor_date = None
        received_from_vendor_date = None
        target_completion_date = None
        actual_completion_date = None

        status_index = statuses.index(status)

        # Set target_completion_date for ALL projects (60-120 days from authorization)
        target_completion_date = authorized_date + timedelta(days=random.randint(60, 120))

        if status_index >= 1:
            sent_to_vendor_date = authorized_date + timedelta(days=random.randint(1, 7))
        if status_index >= 2 and sent_to_vendor_date:
            received_from_vendor_date = sent_to_vendor_date + timedelta(days=random.randint(7, 30))
        if status_index >= 5:
            # Construction ready - set actual completion date
            if random.random() > 0.3:
                actual_completion_date = target_completion_date + timedelta(days=random.randint(-10, 20))

        # Generate budget (between $25,000 and $500,000)
        budget = round(random.uniform(25000, 500000), 2)
        # Actual spend is 0-120% of budget depending on status
        spend_ratio = status_index / len(statuses)  # Progress through workflow
        actual_spend = round(budget * spend_ratio * random.uniform(0.8, 1.2), 2)

        desc_template = random.choice(PROJECT_DESCRIPTIONS)
        description = desc_template.format(region=region).replace("'", "''")

        # Format dates for SQL
        auth_dt = f"'{authorized_date}'" if authorized_date else "NULL"
        sent_dt = f"'{sent_to_vendor_date}'" if sent_to_vendor_date else "NULL"
        recv_dt = f"'{received_from_vendor_date}'" if received_from_vendor_date else "NULL"
        target_dt = f"'{target_completion_date}'" if target_completion_date else "NULL"
        actual_dt = f"'{actual_completion_date}'" if actual_completion_date else "NULL"

        query = f"""
        INSERT INTO {db.table_name('projects')}
        (id, work_order_number, vendor_id, description, region, status, priority,
         authorized_date, sent_to_vendor_date, received_from_vendor_date,
         target_completion_date, actual_completion_date, revision_count, version,
         budget, actual_spend, created_at, updated_at)
        VALUES ('{project_id}', 'WO-2024{i+1:04d}', '{vendor_id}', '{description}',
                '{region}', '{status}', '{priority}', {auth_dt}, {sent_dt}, {recv_dt},
                {target_dt}, {actual_dt}, {random.randint(0, 5)}, 1,
                {budget}, {actual_spend}, '{now}', '{now}')
        """
        db.execute_write(query)

    print(f"Seeded {len(project_ids)} projects")
    return project_ids


def seed_milestones(project_ids: list[str]) -> int:
    """Seed milestone records for each project."""
    count = 0
    stages = MilestoneStage.ALL
    sla_thresholds = MilestoneStage.SLA_THRESHOLDS
    now = datetime.utcnow().isoformat()

    # Get project statuses
    projects = db.execute(f"SELECT id, status, authorized_date FROM {db.table_name('projects')}")
    project_map = {p['id']: p for p in projects}

    for project_id in project_ids:
        project = project_map.get(project_id, {})
        status = project.get('status', ProjectStatus.AUTHORIZED)
        status_index = ProjectStatus.ALL.index(status) if status in ProjectStatus.ALL else 0
        base_date = project.get('authorized_date') or date.today()

        for i, stage in enumerate(stages):
            milestone_id = str(uuid.uuid4())
            expected_date = base_date + timedelta(days=i * 14)
            actual_date = None
            is_overdue = False
            days_overdue = 0

            if i <= status_index:
                actual_date = expected_date + timedelta(days=random.randint(-3, 5))

            if actual_date is None and expected_date < date.today():
                is_overdue = True
                days_overdue = (date.today() - expected_date).days

            sla_days = sla_thresholds.get(stage)
            sla_str = str(sla_days) if sla_days else "NULL"
            actual_str = f"'{actual_date}'" if actual_date else "NULL"

            query = f"""
            INSERT INTO {db.table_name('milestones')}
            (id, project_id, stage, expected_date, actual_date, sla_days,
             is_overdue, days_overdue, created_at, updated_at)
            VALUES ('{milestone_id}', '{project_id}', '{stage}', '{expected_date}',
                    {actual_str}, {sla_str}, {str(is_overdue).lower()}, {days_overdue},
                    '{now}', '{now}')
            """
            db.execute_write(query)
            count += 1

    print(f"Seeded {count} milestones")
    return count


def seed_alerts(project_ids: list[str]) -> int:
    """Seed alert records for projects with issues."""
    count = 0
    alert_types = AlertType.ALL
    severities = AlertSeverity.ALL

    # Get project work order numbers
    projects = db.execute(f"SELECT id, work_order_number FROM {db.table_name('projects')}")
    wo_map = {p['id']: p['work_order_number'] for p in projects}

    for project_id in project_ids:
        if random.random() > 0.7:
            num_alerts = random.randint(1, 3)
            wo = wo_map.get(project_id, project_id[:8])

            for _ in range(num_alerts):
                alert_id = str(uuid.uuid4())
                alert_type = random.choice(alert_types)
                severity = random.choice(severities)
                is_ack = random.random() > 0.5
                created_at = (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat()

                messages = {
                    AlertType.MILESTONE_OVERDUE: f"Milestone overdue for project {wo}",
                    AlertType.MILESTONE_APPROACHING: f"Milestone approaching deadline for {wo}",
                    AlertType.STATUS_CHANGE: f"Status changed for project {wo}",
                    AlertType.REVISION_ADDED: f"New revision submitted for {wo}",
                }
                message = messages[alert_type].replace("'", "''")

                ack_at = f"'{datetime.utcnow().isoformat()}'" if is_ack else "NULL"
                ack_by = "'system@gpc.com'" if is_ack else "NULL"

                query = f"""
                INSERT INTO {db.table_name('alerts')}
                (id, project_id, alert_type, message, severity, is_acknowledged,
                 acknowledged_at, acknowledged_by, created_at)
                VALUES ('{alert_id}', '{project_id}', '{alert_type}', '{message}',
                        '{severity}', {str(is_ack).lower()}, {ack_at}, {ack_by}, '{created_at}')
                """
                db.execute_write(query)
                count += 1

    print(f"Seeded {count} alerts")
    return count


def seed_audit_logs(project_ids: list[str]) -> int:
    """Seed audit log records for projects."""
    count = 0
    actions = AuditAction.ALL

    for project_id in project_ids:
        num_logs = random.randint(2, 5)
        for i in range(num_logs):
            log_id = str(uuid.uuid4())
            action = random.choice(actions)
            created_at = (datetime.utcnow() - timedelta(days=random.randint(0, 60))).isoformat()
            user_num = random.randint(1, 10)

            field_name = "'status'" if action == AuditAction.STATUS_CHANGE else "NULL"
            old_val = f"'{ProjectStatus.ALL[max(0, i-1)]}'" if action == AuditAction.STATUS_CHANGE else "NULL"
            new_val = f"'{ProjectStatus.ALL[min(i, len(ProjectStatus.ALL)-1)]}'" if action == AuditAction.STATUS_CHANGE else "NULL"

            query = f"""
            INSERT INTO {db.table_name('audit_logs')}
            (id, project_id, action, field_name, old_value, new_value, changes,
             user_id, user_email, created_at)
            VALUES ('{log_id}', '{project_id}', '{action}', {field_name}, {old_val},
                    {new_val}, NULL, 'user{user_num}@gpc.com', 'user{user_num}@gpc.com',
                    '{created_at}')
            """
            db.execute_write(query)
            count += 1

    print(f"Seeded {count} audit logs")
    return count


def seed_vendor_metrics(vendor_ids: list[str]) -> int:
    """Seed vendor metric records."""
    count = 0
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=30)
    now = datetime.utcnow().isoformat()

    for vendor_id in vendor_ids:
        metric_id = str(uuid.uuid4())
        total = random.randint(20, 80)
        completed = random.randint(10, total - 5)
        active = total - completed
        overdue = random.randint(0, min(10, active))

        on_time_rate = round(random.uniform(70, 98), 2)
        avg_cycle = round(random.uniform(30, 90), 1)
        revision_rate = round(random.uniform(0.5, 2.5), 2)
        sla_rate = round(random.uniform(75, 99), 2)

        query = f"""
        INSERT INTO {db.table_name('vendor_metrics')}
        (id, vendor_id, period_start, period_end, total_projects, completed_projects,
         active_projects, overdue_projects, on_time_rate, avg_cycle_time_days,
         revision_rate, sla_compliance_rate, created_at, updated_at)
        VALUES ('{metric_id}', '{vendor_id}', '{period_start.isoformat()}',
                '{period_end.isoformat()}', {total}, {completed}, {active}, {overdue},
                {on_time_rate}, {avg_cycle}, {revision_rate}, {sla_rate},
                '{now}', '{now}')
        """
        db.execute_write(query)
        count += 1

    print(f"Seeded {count} vendor metrics")
    return count


def seed_all() -> dict:
    """Seed all tables with mock data."""
    print("Starting database seeding...")

    # Seed in order of dependencies
    vendor_ids = seed_vendors()
    project_ids = seed_projects(vendor_ids, count=50)
    milestone_count = seed_milestones(project_ids)
    alert_count = seed_alerts(project_ids)
    audit_count = seed_audit_logs(project_ids)
    metric_count = seed_vendor_metrics(vendor_ids)

    print("Database seeding complete!")

    return {
        "vendors": len(vendor_ids),
        "projects": len(project_ids),
        "milestones": milestone_count,
        "alerts": alert_count,
        "audit_logs": audit_count,
        "vendor_metrics": metric_count,
    }


def clear_all() -> None:
    """Clear all data from tables (use with caution)."""
    print("Clearing all data...")
    tables = ['vendor_metrics', 'audit_logs', 'alerts', 'milestones', 'projects', 'vendors']
    for table in tables:
        db.execute_write(f"DELETE FROM {db.table_name(table)}")
    print("All data cleared!")
