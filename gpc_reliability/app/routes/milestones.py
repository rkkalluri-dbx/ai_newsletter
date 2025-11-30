"""Milestones API endpoints."""
import uuid
from datetime import datetime, date
from flask import Blueprint, request, jsonify

from app.database import db

milestones_bp = Blueprint("milestones", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


@milestones_bp.route("", methods=["GET"])
def list_milestones():
    """List milestones with filtering.

    Query params:
        - project_id: Filter by project ID
        - stage: Filter by stage (comma-separated)
        - is_overdue: Filter by overdue status (true/false)
        - completed: Filter by completion status (true/false)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
    """
    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)
    offset = (page - 1) * per_page

    # Build WHERE clause
    conditions = []

    # Project filter
    project_id = request.args.get("project_id")
    if project_id:
        conditions.append(f"m.project_id = '{project_id}'")

    # Stage filter
    stage = request.args.get("stage")
    if stage:
        stages = [f"'{s.strip()}'" for s in stage.split(",")]
        conditions.append(f"m.stage IN ({','.join(stages)})")

    # Overdue filter
    is_overdue = request.args.get("is_overdue")
    if is_overdue is not None:
        overdue_value = is_overdue.lower() == "true"
        conditions.append(f"m.is_overdue = {str(overdue_value).lower()}")

    # Completed filter
    completed = request.args.get("completed")
    if completed is not None:
        if completed.lower() == "true":
            conditions.append("m.actual_date IS NOT NULL")
        else:
            conditions.append("m.actual_date IS NULL")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM {table_name('milestones')} m
        WHERE {where_clause}
    """
    count_result = db.execute(count_query)
    total = count_result[0]["total"] if count_result else 0

    # Get paginated data
    data_query = f"""
        SELECT m.*, p.work_order_number, p.status as project_status
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        WHERE {where_clause}
        ORDER BY m.expected_date ASC
        LIMIT {per_page} OFFSET {offset}
    """
    rows = db.execute(data_query)

    milestones = []
    for row in rows:
        expected_date = row["expected_date"].isoformat() if row.get("expected_date") else None
        actual_date = row["actual_date"].isoformat() if row.get("actual_date") else None
        milestones.append({
            "id": row["id"],
            "milestone_id": row["id"],  # Alias for frontend
            "milestone_name": row["stage"].replace("_", " ").title(),  # Alias for frontend
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "project_status": row.get("project_status"),
            "stage": row["stage"],
            "expected_date": expected_date,
            "target_date": expected_date,  # Alias for frontend
            "actual_date": actual_date,
            "completed": actual_date is not None,  # Alias for frontend
            "sla_days": row.get("sla_days"),
            "is_overdue": row.get("is_overdue", False),
            "days_overdue": row.get("days_overdue", 0),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        })

    return jsonify({
        "data": milestones,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


@milestones_bp.route("/<milestone_id>", methods=["GET"])
def get_milestone(milestone_id):
    """Get milestone details by ID."""
    query = f"""
        SELECT m.*, p.work_order_number, p.status as project_status
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        WHERE m.id = '{milestone_id}'
    """
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Milestone not found"}), 404

    row = rows[0]
    return jsonify({
        "data": {
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "project_status": row.get("project_status"),
            "stage": row["stage"],
            "expected_date": row["expected_date"].isoformat() if row.get("expected_date") else None,
            "actual_date": row["actual_date"].isoformat() if row.get("actual_date") else None,
            "sla_days": row.get("sla_days"),
            "is_overdue": row.get("is_overdue", False),
            "days_overdue": row.get("days_overdue", 0),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None
        }
    })


@milestones_bp.route("/<milestone_id>/complete", methods=["POST"])
def complete_milestone(milestone_id):
    """Mark a milestone as complete.

    Request body (optional):
        - actual_date: Completion date (default: today)
    """
    # Check if milestone exists
    query = f"SELECT * FROM {table_name('milestones')} WHERE id = '{milestone_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Milestone not found"}), 404

    current = rows[0]

    if current.get("actual_date"):
        return jsonify({"message": "Milestone already completed"}), 200

    # Get actual date from request - ALWAYS use today's date from server to ensure consistency
    data = request.get_json() or {}
    # Use server's today date to avoid timezone issues
    actual_date = date.today().isoformat()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Log for debugging
    import logging
    logging.info(f"Completing milestone {milestone_id} with actual_date={actual_date}, request_date={data.get('actual_date')}")

    update_query = f"""
        UPDATE {table_name('milestones')}
        SET actual_date = '{actual_date}',
            is_overdue = false,
            days_overdue = 0,
            updated_at = '{now}'
        WHERE id = '{milestone_id}'
    """
    db.execute_write(update_query)

    return get_milestone(milestone_id)


@milestones_bp.route("/<milestone_id>", methods=["PATCH"])
def update_milestone(milestone_id):
    """Update milestone details.

    Request body:
        - expected_date: Expected completion date
        - actual_date: Actual completion date
        - sla_days: SLA days
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Check if milestone exists
    query = f"SELECT * FROM {table_name('milestones')} WHERE id = '{milestone_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Milestone not found"}), 404

    current = rows[0]

    # Build UPDATE statement
    updates = []
    updatable_fields = ["expected_date", "actual_date", "sla_days"]

    for field in updatable_fields:
        if field in data:
            new_value = data[field]
            if new_value is None:
                updates.append(f"{field} = NULL")
            elif field == "sla_days":
                updates.append(f"{field} = {new_value}")
            else:
                updates.append(f"{field} = '{new_value}'")

    if not updates:
        return jsonify({"message": "No changes to apply"}), 200

    # Recalculate overdue status
    expected_date = data.get("expected_date", current.get("expected_date"))
    actual_date = data.get("actual_date", current.get("actual_date"))

    if actual_date:
        updates.append("is_overdue = false")
        updates.append("days_overdue = 0")
    elif expected_date:
        try:
            exp_date = datetime.strptime(str(expected_date)[:10], "%Y-%m-%d").date()
            today = date.today()
            if exp_date < today:
                days_overdue = (today - exp_date).days
                updates.append("is_overdue = true")
                updates.append(f"days_overdue = {days_overdue}")
            else:
                updates.append("is_overdue = false")
                updates.append("days_overdue = 0")
        except ValueError:
            pass

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    updates.append(f"updated_at = '{now}'")

    update_query = f"""
        UPDATE {table_name('milestones')}
        SET {', '.join(updates)}
        WHERE id = '{milestone_id}'
    """
    db.execute_write(update_query)

    return get_milestone(milestone_id)


@milestones_bp.route("/overdue", methods=["GET"])
def get_overdue_milestones():
    """Get all overdue milestones with project details.

    Query params:
        - limit: Maximum items to return (default: 50)
    """
    limit = min(request.args.get("limit", 50, type=int), 100)

    query = f"""
        SELECT m.*, p.work_order_number, p.priority, v.name as vendor_name
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE m.is_overdue = true AND m.actual_date IS NULL
        ORDER BY
            CASE p.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
            END,
            m.days_overdue DESC
        LIMIT {limit}
    """
    rows = db.execute(query)

    milestones = []
    for row in rows:
        milestones.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "vendor_name": row.get("vendor_name"),
            "priority": row.get("priority"),
            "stage": row["stage"],
            "expected_date": row["expected_date"].isoformat() if row.get("expected_date") else None,
            "days_overdue": row.get("days_overdue", 0),
            "sla_days": row.get("sla_days")
        })

    return jsonify({
        "data": milestones,
        "total": len(milestones)
    })


@milestones_bp.route("/upcoming", methods=["GET"])
def get_upcoming_milestones():
    """Get milestones due within the specified days.

    Query params:
        - days: Number of days to look ahead (default: 7)
        - limit: Maximum items to return (default: 50)
    """
    days = request.args.get("days", 7, type=int)
    limit = min(request.args.get("limit", 50, type=int), 100)

    today = date.today()
    future_date = today + datetime.timedelta(days=days) if hasattr(datetime, 'timedelta') else date.today()

    # Import timedelta properly
    from datetime import timedelta
    future_date = today + timedelta(days=days)

    query = f"""
        SELECT m.*, p.work_order_number, p.priority, v.name as vendor_name
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE m.actual_date IS NULL
          AND m.expected_date BETWEEN '{today}' AND '{future_date}'
        ORDER BY m.expected_date ASC
        LIMIT {limit}
    """
    rows = db.execute(query)

    milestones = []
    for row in rows:
        days_until = (row["expected_date"] - today).days if row.get("expected_date") else 0
        milestones.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "vendor_name": row.get("vendor_name"),
            "priority": row.get("priority"),
            "stage": row["stage"],
            "expected_date": row["expected_date"].isoformat() if row.get("expected_date") else None,
            "days_until": days_until,
            "sla_days": row.get("sla_days")
        })

    return jsonify({
        "data": milestones,
        "total": len(milestones)
    })
