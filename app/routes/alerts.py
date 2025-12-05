"""Alerts API endpoints."""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.database import db

alerts_bp = Blueprint("alerts", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


@alerts_bp.route("", methods=["GET"])
def list_alerts():
    """List all alerts with optional filtering.

    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 25, max: 100)
        - severity: Filter by severity (comma-separated: info, warning, critical)
        - alert_type: Filter by type (comma-separated)
        - acknowledged: Filter by acknowledgment status (true/false)
        - project_id: Filter by project ID
        - sort_by: Sort field (default: created_at)
        - sort_order: asc or desc (default: desc)
    """
    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    offset = (page - 1) * per_page

    # Build WHERE clause
    conditions = []

    # Severity filter
    severity = request.args.get("severity")
    if severity:
        severities = [f"'{s.strip()}'" for s in severity.split(",")]
        conditions.append(f"a.severity IN ({','.join(severities)})")

    # Alert type filter
    alert_type = request.args.get("alert_type")
    if alert_type:
        types = [f"'{t.strip()}'" for t in alert_type.split(",")]
        conditions.append(f"a.alert_type IN ({','.join(types)})")

    # Acknowledged filter
    acknowledged = request.args.get("acknowledged")
    if acknowledged is not None:
        ack_value = acknowledged.lower() == "true"
        conditions.append(f"a.is_acknowledged = {str(ack_value).lower()}")

    # Project filter
    project_id = request.args.get("project_id")
    if project_id:
        conditions.append(f"a.project_id = '{project_id}'")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Sorting
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    valid_sort_fields = ["created_at", "severity", "alert_type", "is_acknowledged"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM {table_name('alerts')} a
        WHERE {where_clause}
    """
    count_result = db.execute(count_query)
    total = count_result[0]["total"] if count_result else 0

    # Get paginated data with project info
    data_query = f"""
        SELECT a.*, p.work_order_number
        FROM {table_name('alerts')} a
        JOIN {table_name('projects')} p ON a.project_id = p.id
        WHERE {where_clause}
        ORDER BY
            CASE a.severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                WHEN 'info' THEN 3
            END,
            a.{sort_by} {sort_order}
        LIMIT {per_page} OFFSET {offset}
    """
    rows = db.execute(data_query)

    alerts = []
    for row in rows:
        alerts.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "alert_type": row["alert_type"],
            "message": row["message"],
            "severity": row["severity"],
            "is_acknowledged": row["is_acknowledged"],
            "acknowledged_at": row["acknowledged_at"].isoformat() if row.get("acknowledged_at") else None,
            "acknowledged_by": row.get("acknowledged_by"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        })

    return jsonify({
        "data": alerts,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


@alerts_bp.route("/<alert_id>", methods=["GET"])
def get_alert(alert_id):
    """Get alert details by ID."""
    query = f"""
        SELECT a.*, p.work_order_number
        FROM {table_name('alerts')} a
        JOIN {table_name('projects')} p ON a.project_id = p.id
        WHERE a.id = '{alert_id}'
    """
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Alert not found"}), 404

    row = rows[0]
    return jsonify({
        "data": {
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "alert_type": row["alert_type"],
            "message": row["message"],
            "severity": row["severity"],
            "is_acknowledged": row["is_acknowledged"],
            "acknowledged_at": row["acknowledged_at"].isoformat() if row.get("acknowledged_at") else None,
            "acknowledged_by": row.get("acknowledged_by"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        }
    })


@alerts_bp.route("/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    """Acknowledge a single alert.

    Request body (optional):
        - user_email: Email of user acknowledging (default: api@system)
    """
    # Check if alert exists
    query = f"SELECT * FROM {table_name('alerts')} WHERE id = '{alert_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Alert not found"}), 404

    if rows[0]["is_acknowledged"]:
        return jsonify({"message": "Alert already acknowledged"}), 200

    # Get user email from request body or default
    data = request.get_json() or {}
    user_email = data.get("user_email", "api@system")
    user_email_escaped = user_email.replace("'", "''")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    update_query = f"""
        UPDATE {table_name('alerts')}
        SET is_acknowledged = true,
            acknowledged_at = '{now}',
            acknowledged_by = '{user_email_escaped}'
        WHERE id = '{alert_id}'
    """
    db.execute_write(update_query)

    return get_alert(alert_id)


@alerts_bp.route("/acknowledge", methods=["POST"])
def bulk_acknowledge():
    """Bulk acknowledge multiple alerts.

    Request body:
        - alert_ids: List of alert IDs to acknowledge (required)
        - user_email: Email of user acknowledging (default: api@system)
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    alert_ids = data.get("alert_ids", [])
    if not alert_ids:
        return jsonify({"error": "alert_ids is required"}), 400

    if not isinstance(alert_ids, list):
        return jsonify({"error": "alert_ids must be a list"}), 400

    user_email = data.get("user_email", "api@system")
    user_email_escaped = user_email.replace("'", "''")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Build IN clause
    ids_list = ",".join([f"'{aid}'" for aid in alert_ids])

    update_query = f"""
        UPDATE {table_name('alerts')}
        SET is_acknowledged = true,
            acknowledged_at = '{now}',
            acknowledged_by = '{user_email_escaped}'
        WHERE id IN ({ids_list})
          AND is_acknowledged = false
    """
    affected = db.execute_write(update_query)

    return jsonify({
        "message": f"Acknowledged {affected} alert(s)",
        "acknowledged_count": affected,
        "requested_count": len(alert_ids)
    })


@alerts_bp.route("", methods=["POST"])
def create_alert():
    """Create a new alert.

    Request body:
        - project_id: Project ID (required)
        - alert_type: Type of alert (required)
        - message: Alert message (required)
        - severity: Severity level (default: info)
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Validate required fields
    required = ["project_id", "alert_type", "message"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Validate project exists
    project_query = f"SELECT id FROM {table_name('projects')} WHERE id = '{data['project_id']}'"
    if not db.execute(project_query):
        return jsonify({"error": "Project not found"}), 404

    # Validate severity
    severity = data.get("severity", "info")
    if severity not in ["info", "warning", "critical"]:
        return jsonify({"error": "Invalid severity. Must be info, warning, or critical"}), 400

    # Validate alert_type
    valid_types = ["milestone_overdue", "milestone_approaching", "status_change", "revision_added"]
    alert_type = data["alert_type"]
    if alert_type not in valid_types:
        return jsonify({"error": f"Invalid alert_type. Must be one of: {', '.join(valid_types)}"}), 400

    # Create alert
    alert_id = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    message = data["message"].replace("'", "''")

    insert_query = f"""
        INSERT INTO {table_name('alerts')}
        (id, project_id, alert_type, message, severity, is_acknowledged, created_at)
        VALUES ('{alert_id}', '{data['project_id']}', '{alert_type}', '{message}',
                '{severity}', false, '{now}')
    """
    db.execute_write(insert_query)

    return get_alert(alert_id)


@alerts_bp.route("/<alert_id>", methods=["DELETE"])
def delete_alert(alert_id):
    """Delete an alert."""
    # Check if alert exists
    query = f"SELECT id FROM {table_name('alerts')} WHERE id = '{alert_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Alert not found"}), 404

    db.execute_write(f"DELETE FROM {table_name('alerts')} WHERE id = '{alert_id}'")

    return jsonify({"message": "Alert deleted successfully"})


@alerts_bp.route("/stats", methods=["GET"])
def get_alert_stats():
    """Get alert statistics.

    Returns counts by severity and type, both total and unacknowledged.
    """
    # By severity
    severity_query = f"""
        SELECT
            severity,
            COUNT(*) as total,
            SUM(CASE WHEN is_acknowledged = false THEN 1 ELSE 0 END) as unacknowledged
        FROM {table_name('alerts')}
        GROUP BY severity
    """
    severity_rows = db.execute(severity_query)

    # By type
    type_query = f"""
        SELECT
            alert_type,
            COUNT(*) as total,
            SUM(CASE WHEN is_acknowledged = false THEN 1 ELSE 0 END) as unacknowledged
        FROM {table_name('alerts')}
        GROUP BY alert_type
    """
    type_rows = db.execute(type_query)

    # Overall stats
    overall_query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_acknowledged = false THEN 1 ELSE 0 END) as unacknowledged,
            SUM(CASE WHEN is_acknowledged = true THEN 1 ELSE 0 END) as acknowledged
        FROM {table_name('alerts')}
    """
    overall_result = db.execute(overall_query)
    overall = overall_result[0] if overall_result else {}

    return jsonify({
        "data": {
            "overall": {
                "total": overall.get("total", 0),
                "unacknowledged": overall.get("unacknowledged", 0),
                "acknowledged": overall.get("acknowledged", 0)
            },
            "by_severity": [
                {
                    "severity": row["severity"],
                    "total": row["total"],
                    "unacknowledged": row["unacknowledged"]
                }
                for row in severity_rows
            ],
            "by_type": [
                {
                    "alert_type": row["alert_type"],
                    "total": row["total"],
                    "unacknowledged": row["unacknowledged"]
                }
                for row in type_rows
            ]
        }
    })
