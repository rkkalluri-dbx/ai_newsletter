"""Projects API endpoints."""
import csv
import io
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, Response

from app.database import db
from app.models.project import Project, ProjectStatus, Priority
from app.models.audit_log import AuditLog, AuditAction

projects_bp = Blueprint("projects", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


@projects_bp.route("", methods=["GET"])
def list_projects():
    """List all projects with pagination and filtering.

    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 25, max: 100)
        - status: Filter by status (comma-separated)
        - vendor_id: Filter by vendor ID
        - region: Filter by region (comma-separated)
        - priority: Filter by priority (comma-separated)
        - date_from: Filter by authorized_date >= date
        - date_to: Filter by authorized_date <= date
        - search: Search in work_order_number and description
        - sort_by: Sort field (default: created_at)
        - sort_order: asc or desc (default: desc)
    """
    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    offset = (page - 1) * per_page

    # Build WHERE clause
    conditions = []

    # Status filter
    status = request.args.get("status")
    if status:
        statuses = [f"'{s.strip()}'" for s in status.split(",")]
        conditions.append(f"status IN ({','.join(statuses)})")

    # Vendor filter
    vendor_id = request.args.get("vendor_id")
    if vendor_id:
        conditions.append(f"vendor_id = '{vendor_id}'")

    # Region filter
    region = request.args.get("region")
    if region:
        regions = [f"'{r.strip()}'" for r in region.split(",")]
        conditions.append(f"region IN ({','.join(regions)})")

    # Priority filter
    priority = request.args.get("priority")
    if priority:
        priorities = [f"'{p.strip()}'" for p in priority.split(",")]
        conditions.append(f"priority IN ({','.join(priorities)})")

    # Date range filters
    date_from = request.args.get("date_from")
    if date_from:
        conditions.append(f"authorized_date >= '{date_from}'")

    date_to = request.args.get("date_to")
    if date_to:
        conditions.append(f"authorized_date <= '{date_to}'")

    # Search filter
    search = request.args.get("search")
    if search:
        search_escaped = search.replace("'", "''")
        conditions.append(f"(work_order_number LIKE '%{search_escaped}%' OR description LIKE '%{search_escaped}%')")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Sorting
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    valid_sort_fields = ["created_at", "updated_at", "work_order_number", "status", "priority", "authorized_date"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM {table_name('projects')} WHERE {where_clause}"
    count_result = db.execute(count_query)
    total = count_result[0]["total"] if count_result else 0

    # Get paginated data
    data_query = f"""
        SELECT p.*, v.name as vendor_name, v.code as vendor_code
        FROM {table_name('projects')} p
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE {where_clause}
        ORDER BY p.{sort_by} {sort_order}
        LIMIT {per_page} OFFSET {offset}
    """
    rows = db.execute(data_query)

    # Convert to dict
    projects = []
    for row in rows:
        project = Project.from_row(row)
        project_dict = project.to_dict()
        project_dict["vendor_name"] = row.get("vendor_name")
        project_dict["vendor_code"] = row.get("vendor_code")
        projects.append(project_dict)

    return jsonify({
        "data": projects,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


@projects_bp.route("/<project_id>", methods=["GET"])
def get_project(project_id):
    """Get project details by ID with milestones."""
    query = f"""
        SELECT p.*, v.name as vendor_name, v.code as vendor_code
        FROM {table_name('projects')} p
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE p.id = '{project_id}'
    """
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Project not found"}), 404

    row = rows[0]
    project = Project.from_row(row)
    project_dict = project.to_dict()
    project_dict["vendor_name"] = row.get("vendor_name")
    project_dict["vendor_code"] = row.get("vendor_code")

    # Get milestones
    milestones_query = f"""
        SELECT * FROM {table_name('milestones')}
        WHERE project_id = '{project_id}'
        ORDER BY expected_date ASC
    """
    milestones_rows = db.execute(milestones_query)
    project_dict["milestones"] = [
        {
            "id": m["id"],
            "stage": m["stage"],
            "expected_date": m["expected_date"].isoformat() if m.get("expected_date") else None,
            "target_date": m["expected_date"].isoformat() if m.get("expected_date") else None,  # Alias for frontend
            "actual_date": m["actual_date"].isoformat() if m.get("actual_date") else None,
            "sla_days": m.get("sla_days"),
            "is_overdue": m.get("is_overdue", False),
            "days_overdue": m.get("days_overdue", 0)
        }
        for m in milestones_rows
    ]

    return jsonify({"data": project_dict})


@projects_bp.route("", methods=["POST"])
def create_project():
    """Create a new project."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Validate required fields
    required = ["work_order_number", "vendor_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Check if work order already exists
    check_query = f"SELECT id FROM {table_name('projects')} WHERE work_order_number = '{data['work_order_number']}'"
    existing = db.execute(check_query)
    if existing:
        return jsonify({"error": "Work order number already exists"}), 409

    # Create project
    project_id = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    status = data.get("status", ProjectStatus.AUTHORIZED)
    priority = data.get("priority", Priority.NORMAL)

    # Format optional date fields
    auth_date = f"'{data['authorized_date']}'" if data.get("authorized_date") else "NULL"
    sent_date = f"'{data['sent_to_vendor_date']}'" if data.get("sent_to_vendor_date") else "NULL"
    recv_date = f"'{data['received_from_vendor_date']}'" if data.get("received_from_vendor_date") else "NULL"
    target_date = f"'{data['target_completion_date']}'" if data.get("target_completion_date") else "NULL"
    actual_date = f"'{data['actual_completion_date']}'" if data.get("actual_completion_date") else "NULL"

    desc = (data.get("description") or "").replace("'", "''")
    region = (data.get("region") or "").replace("'", "''")

    insert_query = f"""
        INSERT INTO {table_name('projects')}
        (id, work_order_number, vendor_id, description, region, status, priority,
         authorized_date, sent_to_vendor_date, received_from_vendor_date,
         target_completion_date, actual_completion_date, revision_count, version,
         created_at, updated_at)
        VALUES ('{project_id}', '{data['work_order_number']}', '{data['vendor_id']}',
                '{desc}', '{region}', '{status}', '{priority}',
                {auth_date}, {sent_date}, {recv_date}, {target_date}, {actual_date},
                0, 1, '{now}', '{now}')
    """
    db.execute_write(insert_query)

    # Create audit log
    audit_id = str(uuid.uuid4())
    audit_query = f"""
        INSERT INTO {table_name('audit_logs')}
        (id, project_id, action, user_id, user_email, created_at)
        VALUES ('{audit_id}', '{project_id}', '{AuditAction.CREATE}', 'api', 'api@system', '{now}')
    """
    db.execute_write(audit_query)

    # Return created project
    return get_project(project_id)


@projects_bp.route("/<project_id>", methods=["PATCH"])
def update_project(project_id):
    """Update project details with optimistic locking."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Get current project
    query = f"SELECT * FROM {table_name('projects')} WHERE id = '{project_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Project not found"}), 404

    current = rows[0]

    # Check version for optimistic locking
    if "version" in data:
        if data["version"] != current["version"]:
            return jsonify({
                "error": "Conflict: Project was modified by another user",
                "current_version": current["version"],
                "your_version": data["version"]
            }), 409

    # Build UPDATE statement
    updates = []
    audit_changes = {}

    updatable_fields = [
        "status", "priority", "description", "region",
        "authorized_date", "sent_to_vendor_date", "received_from_vendor_date",
        "target_completion_date", "actual_completion_date", "revision_count"
    ]

    for field in updatable_fields:
        if field in data:
            old_value = current.get(field)
            new_value = data[field]

            if old_value != new_value:
                audit_changes[field] = {"old": str(old_value), "new": str(new_value)}

                if new_value is None:
                    updates.append(f"{field} = NULL")
                elif isinstance(new_value, str):
                    updates.append(f"{field} = '{new_value.replace(chr(39), chr(39)+chr(39))}'")
                else:
                    updates.append(f"{field} = {new_value}")

    if not updates:
        return jsonify({"message": "No changes to apply"}), 200

    # Increment version and update timestamp
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    new_version = current["version"] + 1
    updates.append(f"version = {new_version}")
    updates.append(f"updated_at = '{now}'")

    update_query = f"""
        UPDATE {table_name('projects')}
        SET {', '.join(updates)}
        WHERE id = '{project_id}' AND version = {current['version']}
    """
    affected = db.execute_write(update_query)

    if affected == 0:
        return jsonify({"error": "Conflict: Project was modified by another user"}), 409

    # Create audit log
    audit_id = str(uuid.uuid4())
    action = AuditAction.STATUS_CHANGE if "status" in audit_changes else AuditAction.UPDATE

    audit_query = f"""
        INSERT INTO {table_name('audit_logs')}
        (id, project_id, action, changes, user_id, user_email, created_at)
        VALUES ('{audit_id}', '{project_id}', '{action}',
                '{str(audit_changes).replace(chr(39), chr(39)+chr(39))}',
                'api', 'api@system', '{now}')
    """
    db.execute_write(audit_query)

    # Return updated project
    return get_project(project_id)


@projects_bp.route("/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project."""
    # Check if project exists
    query = f"SELECT id FROM {table_name('projects')} WHERE id = '{project_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Project not found"}), 404

    # Delete related records first (milestones, alerts, audit_logs)
    db.execute_write(f"DELETE FROM {table_name('milestones')} WHERE project_id = '{project_id}'")
    db.execute_write(f"DELETE FROM {table_name('alerts')} WHERE project_id = '{project_id}'")
    db.execute_write(f"DELETE FROM {table_name('audit_logs')} WHERE project_id = '{project_id}'")

    # Delete project
    db.execute_write(f"DELETE FROM {table_name('projects')} WHERE id = '{project_id}'")

    return jsonify({"message": "Project deleted successfully"})


@projects_bp.route("/<project_id>/history", methods=["GET"])
def get_project_history(project_id):
    """Get project audit history."""
    # Check if project exists
    check_query = f"SELECT id FROM {table_name('projects')} WHERE id = '{project_id}'"
    if not db.execute(check_query):
        return jsonify({"error": "Project not found"}), 404

    query = f"""
        SELECT * FROM {table_name('audit_logs')}
        WHERE project_id = '{project_id}'
        ORDER BY created_at DESC
    """
    rows = db.execute(query)

    history = [
        {
            "id": row["id"],
            "event_type": row["action"],  # Frontend expects event_type
            "old_value": row.get("old_value"),
            "new_value": row.get("new_value"),
            "details": row.get("changes") or row.get("field_name"),
            "changed_by": row.get("user_email"),  # Frontend expects changed_by
            "changed_at": row["created_at"].isoformat() if row.get("created_at") else None  # Frontend expects changed_at
        }
        for row in rows
    ]

    return jsonify({"data": history})


@projects_bp.route("/export", methods=["GET"])
def export_projects():
    """Export projects to CSV with same filters as list."""
    # Build WHERE clause (same as list_projects)
    conditions = []

    status = request.args.get("status")
    if status:
        statuses = [f"'{s.strip()}'" for s in status.split(",")]
        conditions.append(f"status IN ({','.join(statuses)})")

    vendor_id = request.args.get("vendor_id")
    if vendor_id:
        conditions.append(f"p.vendor_id = '{vendor_id}'")

    region = request.args.get("region")
    if region:
        regions = [f"'{r.strip()}'" for r in region.split(",")]
        conditions.append(f"region IN ({','.join(regions)})")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT p.work_order_number, v.name as vendor_name, p.status, p.priority,
               p.region, p.authorized_date, p.sent_to_vendor_date,
               p.received_from_vendor_date, p.target_completion_date,
               p.actual_completion_date, p.revision_count
        FROM {table_name('projects')} p
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE {where_clause}
        ORDER BY p.work_order_number
    """
    rows = db.execute(query)

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Work Order", "Vendor", "Status", "Priority", "Region",
        "Authorized Date", "Sent to Vendor", "Received from Vendor",
        "Target Completion", "Actual Completion", "Revisions"
    ])

    # Data rows
    for row in rows:
        writer.writerow([
            row.get("work_order_number"),
            row.get("vendor_name"),
            row.get("status"),
            row.get("priority"),
            row.get("region"),
            row.get("authorized_date"),
            row.get("sent_to_vendor_date"),
            row.get("received_from_vendor_date"),
            row.get("target_completion_date"),
            row.get("actual_completion_date"),
            row.get("revision_count")
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=projects_export.csv"}
    )


@projects_bp.route("/admin/fix-target-dates", methods=["POST"])
def fix_target_dates():
    """Admin endpoint to fix missing target_completion_date values."""
    # Update projects with NULL target_completion_date
    # Set it to 90 days after authorized_date
    query = f"""
        UPDATE {table_name('projects')}
        SET target_completion_date = DATE_ADD(authorized_date, 90)
        WHERE target_completion_date IS NULL
          AND authorized_date IS NOT NULL
    """
    affected = db.execute_write(query)

    return jsonify({
        "message": f"Updated {affected} projects with target_completion_date"
    })


@projects_bp.route("/admin/seed-budgets", methods=["POST"])
def seed_budgets():
    """Admin endpoint to seed budget values for existing projects."""
    import random

    # Get all projects that need budget values
    query = f"""
        SELECT id, status FROM {table_name('projects')}
        WHERE budget IS NULL OR budget = 0
    """
    projects = db.execute(query)

    if not projects:
        return jsonify({"message": "No projects need budget updates", "updated": 0})

    statuses = ProjectStatus.ALL
    updated = 0

    for project in projects:
        project_id = project["id"]
        status = project.get("status", ProjectStatus.AUTHORIZED)
        status_index = statuses.index(status) if status in statuses else 0

        # Generate budget (between $25,000 and $500,000)
        budget = round(random.uniform(25000, 500000), 2)
        # Actual spend is 0-120% of budget depending on status
        spend_ratio = status_index / len(statuses)
        actual_spend = round(budget * spend_ratio * random.uniform(0.8, 1.2), 2)

        update_query = f"""
            UPDATE {table_name('projects')}
            SET budget = {budget}, actual_spend = {actual_spend}
            WHERE id = '{project_id}'
        """
        db.execute_write(update_query)
        updated += 1

    return jsonify({
        "message": f"Updated {updated} projects with budget values",
        "updated": updated
    })
