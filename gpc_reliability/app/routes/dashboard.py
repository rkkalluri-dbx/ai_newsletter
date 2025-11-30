"""Dashboard API endpoints."""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app.database import db

dashboard_bp = Blueprint("dashboard", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


@dashboard_bp.route("/summary", methods=["GET"])
def get_summary():
    """Get dashboard summary metrics.

    Returns aggregate counts and key metrics for the dashboard overview.
    """
    # Project counts by status
    status_query = f"""
        SELECT
            COUNT(*) as total_projects,
            SUM(CASE WHEN status = 'construction_ready' THEN 1 ELSE 0 END) as completed_projects,
            SUM(CASE WHEN status != 'construction_ready' THEN 1 ELSE 0 END) as active_projects,
            SUM(CASE WHEN priority = 'critical' THEN 1 ELSE 0 END) as critical_projects,
            SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_priority_projects
        FROM {table_name('projects')}
    """
    status_result = db.execute(status_query)

    # Overdue milestones count
    overdue_query = f"""
        SELECT COUNT(DISTINCT project_id) as overdue_projects
        FROM {table_name('milestones')}
        WHERE is_overdue = true AND actual_date IS NULL
    """
    overdue_result = db.execute(overdue_query)

    # Status breakdown
    breakdown_query = f"""
        SELECT status, COUNT(*) as count
        FROM {table_name('projects')}
        GROUP BY status
        ORDER BY count DESC
    """
    breakdown_result = db.execute(breakdown_query)

    # Unacknowledged alerts
    alerts_query = f"""
        SELECT
            COUNT(*) as total_alerts,
            SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_alerts,
            SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) as warning_alerts
        FROM {table_name('alerts')}
        WHERE is_acknowledged = false
    """
    alerts_result = db.execute(alerts_query)

    # Vendor count
    vendor_query = f"SELECT COUNT(*) as count FROM {table_name('vendors')} WHERE is_active = true"
    vendor_result = db.execute(vendor_query)

    # Build response
    status_data = status_result[0] if status_result else {}
    overdue_data = overdue_result[0] if overdue_result else {}
    alerts_data = alerts_result[0] if alerts_result else {}
    vendor_data = vendor_result[0] if vendor_result else {}

    return jsonify({
        "data": {
            "projects": {
                "total": status_data.get("total_projects", 0),
                "active": status_data.get("active_projects", 0),
                "completed": status_data.get("completed_projects", 0),
                "overdue": overdue_data.get("overdue_projects", 0),
                "critical": status_data.get("critical_projects", 0),
                "high_priority": status_data.get("high_priority_projects", 0)
            },
            "alerts": {
                "unacknowledged": alerts_data.get("total_alerts", 0),
                "critical": alerts_data.get("critical_alerts", 0),
                "warning": alerts_data.get("warning_alerts", 0)
            },
            "vendors": {
                "active": vendor_data.get("count", 0)
            },
            "status_breakdown": [
                {"status": row["status"], "count": row["count"]}
                for row in breakdown_result
            ]
        }
    })


@dashboard_bp.route("/next-actions", methods=["GET"])
def get_next_actions():
    """Get prioritized next actions list.

    Returns a list of actionable items that need attention,
    prioritized by urgency and importance.

    Query params:
        - limit: Maximum items to return (default: 10, max: 50)
    """
    limit = min(request.args.get("limit", 10, type=int), 50)

    # Priority order: critical alerts, overdue milestones, approaching milestones
    actions = []

    # 1. Critical unacknowledged alerts
    critical_alerts_query = f"""
        SELECT a.*, p.work_order_number
        FROM {table_name('alerts')} a
        JOIN {table_name('projects')} p ON a.project_id = p.id
        WHERE a.is_acknowledged = false AND a.severity = 'critical'
        ORDER BY a.created_at DESC
        LIMIT 10
    """
    critical_alerts = db.execute(critical_alerts_query)
    for alert in critical_alerts:
        actions.append({
            "type": "critical_alert",
            "priority": 1,
            "title": f"Critical Alert: {alert.get('message', 'Alert')}",
            "description": f"Work Order: {alert.get('work_order_number')}",
            "project_id": alert["project_id"],
            "work_order_number": alert.get("work_order_number"),
            "alert_id": alert["id"],
            "created_at": alert["created_at"].isoformat() if alert.get("created_at") else None
        })

    # 2. Overdue milestones
    overdue_query = f"""
        SELECT m.*, p.work_order_number, p.priority as project_priority
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        WHERE m.is_overdue = true AND m.actual_date IS NULL
        ORDER BY
            CASE p.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
            END,
            m.days_overdue DESC
        LIMIT 15
    """
    overdue_milestones = db.execute(overdue_query)
    for milestone in overdue_milestones:
        actions.append({
            "type": "overdue_milestone",
            "priority": 2,
            "title": f"Overdue: {milestone.get('stage', 'Milestone').replace('_', ' ').title()}",
            "description": f"{milestone.get('days_overdue', 0)} days overdue - {milestone.get('work_order_number')}",
            "project_id": milestone["project_id"],
            "work_order_number": milestone.get("work_order_number"),
            "milestone_id": milestone["id"],
            "stage": milestone.get("stage"),
            "days_overdue": milestone.get("days_overdue", 0),
            "expected_date": milestone["expected_date"].isoformat() if milestone.get("expected_date") else None
        })

    # 3. Approaching milestones (within 3 days)
    today = datetime.utcnow().date()
    upcoming_date = (datetime.utcnow() + timedelta(days=3)).date()
    approaching_query = f"""
        SELECT m.*, p.work_order_number, p.priority as project_priority
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        WHERE m.actual_date IS NULL
          AND m.expected_date BETWEEN '{today}' AND '{upcoming_date}'
        ORDER BY m.expected_date ASC
        LIMIT 10
    """
    approaching = db.execute(approaching_query)
    for milestone in approaching:
        days_until = (milestone["expected_date"] - today).days if milestone.get("expected_date") else 0
        actions.append({
            "type": "approaching_milestone",
            "priority": 3,
            "title": f"Due Soon: {milestone.get('stage', 'Milestone').replace('_', ' ').title()}",
            "description": f"Due in {days_until} day(s) - {milestone.get('work_order_number')}",
            "project_id": milestone["project_id"],
            "work_order_number": milestone.get("work_order_number"),
            "milestone_id": milestone["id"],
            "stage": milestone.get("stage"),
            "days_until": days_until,
            "expected_date": milestone["expected_date"].isoformat() if milestone.get("expected_date") else None
        })

    # 4. Warning alerts
    warning_alerts_query = f"""
        SELECT a.*, p.work_order_number
        FROM {table_name('alerts')} a
        JOIN {table_name('projects')} p ON a.project_id = p.id
        WHERE a.is_acknowledged = false AND a.severity = 'warning'
        ORDER BY a.created_at DESC
        LIMIT 10
    """
    warning_alerts = db.execute(warning_alerts_query)
    for alert in warning_alerts:
        actions.append({
            "type": "warning_alert",
            "priority": 4,
            "title": f"Warning: {alert.get('message', 'Alert')}",
            "description": f"Work Order: {alert.get('work_order_number')}",
            "project_id": alert["project_id"],
            "work_order_number": alert.get("work_order_number"),
            "alert_id": alert["id"],
            "created_at": alert["created_at"].isoformat() if alert.get("created_at") else None
        })

    # Sort by priority and limit
    actions.sort(key=lambda x: (x["priority"], x.get("days_overdue", 0) * -1))
    actions = actions[:limit]

    return jsonify({
        "data": actions,
        "total": len(actions)
    })


@dashboard_bp.route("/status-distribution", methods=["GET"])
def get_status_distribution():
    """Get project count by status for charts."""
    query = f"""
        SELECT status, COUNT(*) as count
        FROM {table_name('projects')}
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'authorized' THEN 1
                WHEN 'assigned_to_vendor' THEN 2
                WHEN 'design_submitted' THEN 3
                WHEN 'qa_qc' THEN 4
                WHEN 'approved' THEN 5
                WHEN 'construction_ready' THEN 6
            END
    """
    rows = db.execute(query)

    # Define all statuses with labels
    status_labels = {
        "authorized": "Authorized",
        "assigned_to_vendor": "Assigned to Vendor",
        "design_submitted": "Design Submitted",
        "qa_qc": "QA/QC",
        "approved": "Approved",
        "construction_ready": "Construction Ready"
    }

    distribution = []
    for row in rows:
        status = row["status"]
        distribution.append({
            "status": status,
            "label": status_labels.get(status, status.replace("_", " ").title()),
            "count": row["count"]
        })

    return jsonify({"data": distribution})


@dashboard_bp.route("/region-distribution", methods=["GET"])
def get_region_distribution():
    """Get project count by region for charts."""
    query = f"""
        SELECT region, COUNT(*) as count
        FROM {table_name('projects')}
        WHERE region IS NOT NULL AND region != ''
        GROUP BY region
        ORDER BY count DESC
    """
    rows = db.execute(query)

    return jsonify({
        "data": [
            {"region": row["region"], "count": row["count"]}
            for row in rows
        ]
    })


@dashboard_bp.route("/vendor-performance", methods=["GET"])
def get_vendor_performance():
    """Get vendor performance summary for dashboard.

    Query params:
        - limit: Number of vendors to return (default: 10)
    """
    limit = min(request.args.get("limit", 10, type=int), 50)

    query = f"""
        SELECT
            v.id as vendor_id,
            v.name as vendor_name,
            v.code as vendor_code,
            COALESCE(ps.total_projects, 0) as total_projects,
            COALESCE(ps.completed, 0) as completed,
            COALESCE(ps.active, 0) as active,
            COALESCE(vm.on_time_rate, 0) as on_time_percentage
        FROM {table_name('vendors')} v
        LEFT JOIN (
            SELECT
                vendor_id,
                COUNT(*) as total_projects,
                SUM(CASE WHEN status = 'construction_ready' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status != 'construction_ready' THEN 1 ELSE 0 END) as active
            FROM {table_name('projects')}
            GROUP BY vendor_id
        ) ps ON v.id = ps.vendor_id
        LEFT JOIN (
            SELECT vendor_id, on_time_rate,
                   ROW_NUMBER() OVER (PARTITION BY vendor_id ORDER BY period_end DESC) as rn
            FROM {table_name('vendor_metrics')}
        ) vm ON v.id = vm.vendor_id AND vm.rn = 1
        WHERE v.is_active = true
        ORDER BY ps.total_projects DESC NULLS LAST
        LIMIT {limit}
    """
    rows = db.execute(query)

    return jsonify({
        "data": [
            {
                "vendor_id": row["vendor_id"],
                "vendor_name": row["vendor_name"],
                "vendor_code": row["vendor_code"],
                "total_projects": row["total_projects"] or 0,
                "completed": row["completed"] or 0,
                "active": row["active"] or 0,
                "on_time_percentage": round(row["on_time_percentage"] or 0, 1)
            }
            for row in rows
        ]
    })


@dashboard_bp.route("/recent-activity", methods=["GET"])
def get_recent_activity():
    """Get recent project activity for dashboard timeline.

    Query params:
        - limit: Number of activities to return (default: 20)
    """
    limit = min(request.args.get("limit", 20, type=int), 100)

    query = f"""
        SELECT
            al.id,
            al.project_id,
            al.action,
            al.field_name,
            al.old_value,
            al.new_value,
            al.user_email,
            al.created_at,
            p.work_order_number
        FROM {table_name('audit_logs')} al
        JOIN {table_name('projects')} p ON al.project_id = p.id
        ORDER BY al.created_at DESC
        LIMIT {limit}
    """
    rows = db.execute(query)

    activities = []
    for row in rows:
        action = row["action"]
        description = action.replace("_", " ").title()

        if action == "status_change" and row.get("old_value") and row.get("new_value"):
            description = f"Status changed from {row['old_value']} to {row['new_value']}"
        elif action == "update" and row.get("field_name"):
            description = f"Updated {row['field_name']}"

        activities.append({
            "id": row["id"],
            "project_id": row["project_id"],
            "work_order_number": row.get("work_order_number"),
            "action": action,
            "description": description,
            "user_email": row.get("user_email"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        })

    return jsonify({
        "data": activities,
        "total": len(activities)
    })
