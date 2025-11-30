"""Gantt chart API endpoints."""
from datetime import date, timedelta
from flask import Blueprint, request, jsonify

from app.database import db

gantt_bp = Blueprint("gantt", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


# Stage order for workflow
STAGE_ORDER = [
    "authorized",
    "assigned_to_vendor",
    "design_submitted",
    "qa_qc",
    "approved",
    "construction_ready"
]


@gantt_bp.route("", methods=["GET"])
def get_gantt_data():
    """Get project data formatted for Gantt chart display.

    Query params:
        - vendor_id: Filter by vendor
        - region: Filter by region (comma-separated)
        - status: Filter by status (comma-separated)
        - priority: Filter by priority (comma-separated)
        - date_from: Start date filter
        - date_to: End date filter
        - limit: Maximum projects to return (default: 100)
    """
    limit = min(request.args.get("limit", 100, type=int), 500)

    # Build WHERE clause
    conditions = []

    vendor_id = request.args.get("vendor_id")
    if vendor_id:
        conditions.append(f"p.vendor_id = '{vendor_id}'")

    region = request.args.get("region")
    if region:
        regions = [f"'{r.strip()}'" for r in region.split(",")]
        conditions.append(f"p.region IN ({','.join(regions)})")

    status = request.args.get("status")
    if status:
        statuses = [f"'{s.strip()}'" for s in status.split(",")]
        conditions.append(f"p.status IN ({','.join(statuses)})")

    priority = request.args.get("priority")
    if priority:
        priorities = [f"'{pr.strip()}'" for pr in priority.split(",")]
        conditions.append(f"p.priority IN ({','.join(priorities)})")

    date_from = request.args.get("date_from")
    if date_from:
        conditions.append(f"p.authorized_date >= '{date_from}'")

    date_to = request.args.get("date_to")
    if date_to:
        conditions.append(f"p.authorized_date <= '{date_to}'")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get projects with vendor info
    projects_query = f"""
        SELECT p.*, v.name as vendor_name, v.code as vendor_code
        FROM {table_name('projects')} p
        LEFT JOIN {table_name('vendors')} v ON p.vendor_id = v.id
        WHERE {where_clause}
        ORDER BY
            CASE p.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
            END,
            p.authorized_date ASC
        LIMIT {limit}
    """
    projects = db.execute(projects_query)

    if not projects:
        return jsonify({"data": [], "total": 0})

    # Get all project IDs for milestone lookup
    project_ids = [p["id"] for p in projects]
    ids_list = ",".join([f"'{pid}'" for pid in project_ids])

    # Get all milestones for these projects
    milestones_query = f"""
        SELECT * FROM {table_name('milestones')}
        WHERE project_id IN ({ids_list})
        ORDER BY project_id, expected_date ASC
    """
    all_milestones = db.execute(milestones_query)

    # Group milestones by project
    milestones_by_project = {}
    for m in all_milestones:
        pid = m["project_id"]
        if pid not in milestones_by_project:
            milestones_by_project[pid] = []
        milestones_by_project[pid].append(m)

    # Build Gantt data structure
    gantt_data = []
    today = date.today()

    for project in projects:
        project_id = project["id"]
        milestones = milestones_by_project.get(project_id, [])

        # Calculate project timeline
        start_date = project.get("authorized_date")
        end_date = project.get("target_completion_date") or project.get("actual_completion_date")

        if not start_date:
            # Skip projects without start date
            continue

        if not end_date:
            # Estimate end date based on milestones
            if milestones:
                milestone_dates = [m["expected_date"] for m in milestones if m.get("expected_date")]
                if milestone_dates:
                    end_date = max(milestone_dates)
                else:
                    end_date = start_date + timedelta(days=90)
            else:
                end_date = start_date + timedelta(days=90)

        # Calculate progress
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.get("actual_date")])
        progress = round((completed_milestones / total_milestones * 100) if total_milestones > 0 else 0, 1)

        # Current stage (based on project status)
        current_stage_index = STAGE_ORDER.index(project["status"]) if project["status"] in STAGE_ORDER else 0

        # Build milestone bars for Gantt
        milestone_bars = []
        for i, stage in enumerate(STAGE_ORDER):
            # Find the milestone for this stage
            stage_milestone = next((m for m in milestones if m["stage"] == stage), None)

            if stage_milestone:
                bar = {
                    "stage": stage,
                    "stage_label": stage.replace("_", " ").title(),
                    "expected_date": stage_milestone["expected_date"].isoformat() if stage_milestone.get("expected_date") else None,
                    "actual_date": stage_milestone["actual_date"].isoformat() if stage_milestone.get("actual_date") else None,
                    "is_complete": stage_milestone.get("actual_date") is not None,
                    "is_current": i == current_stage_index,
                    "is_overdue": stage_milestone.get("is_overdue", False),
                    "days_overdue": stage_milestone.get("days_overdue", 0),
                    "sla_days": stage_milestone.get("sla_days")
                }
            else:
                # Create placeholder for missing milestone
                bar = {
                    "stage": stage,
                    "stage_label": stage.replace("_", " ").title(),
                    "expected_date": None,
                    "actual_date": None,
                    "is_complete": i < current_stage_index,
                    "is_current": i == current_stage_index,
                    "is_overdue": False,
                    "days_overdue": 0,
                    "sla_days": None
                }

            milestone_bars.append(bar)

        # Check if project has any overdue milestones
        has_overdue = any(m.get("is_overdue") for m in milestones if not m.get("actual_date"))

        gantt_data.append({
            "id": project_id,
            "work_order_number": project["work_order_number"],
            "description": project.get("description"),
            "vendor_id": project.get("vendor_id"),
            "vendor_name": project.get("vendor_name"),
            "vendor_code": project.get("vendor_code"),
            "region": project.get("region"),
            "status": project["status"],
            "status_label": project["status"].replace("_", " ").title(),
            "priority": project["priority"],
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "target_date": project["target_completion_date"].isoformat() if project.get("target_completion_date") else None,
            "actual_completion_date": project["actual_completion_date"].isoformat() if project.get("actual_completion_date") else None,
            "progress": progress,
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "has_overdue": has_overdue,
            "milestones": milestone_bars
        })

    return jsonify({
        "data": gantt_data,
        "total": len(gantt_data),
        "stages": [{"id": s, "label": s.replace("_", " ").title()} for s in STAGE_ORDER]
    })


@gantt_bp.route("/timeline", methods=["GET"])
def get_timeline_view():
    """Get simplified timeline data for calendar view.

    Query params:
        - start_date: Start of timeline range
        - end_date: End of timeline range
        - view: 'week', 'month', or 'quarter' (default: month)
    """
    view = request.args.get("view", "month")

    today = date.today()

    # Determine date range
    if view == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif view == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = date(today.year, quarter_start_month, 1)
        # End of quarter
        if quarter_start_month == 10:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, quarter_start_month + 3, 1) - timedelta(days=1)
    else:  # month
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # Override with query params if provided
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    if start_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_str:
        try:
            from datetime import datetime
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Get milestones in the date range
    query = f"""
        SELECT m.*, p.work_order_number, p.priority, p.status as project_status
        FROM {table_name('milestones')} m
        JOIN {table_name('projects')} p ON m.project_id = p.id
        WHERE (m.expected_date BETWEEN '{start_date}' AND '{end_date}'
               OR m.actual_date BETWEEN '{start_date}' AND '{end_date}')
        ORDER BY m.expected_date ASC
    """
    milestones = db.execute(query)

    # Group by date
    events_by_date = {}
    for m in milestones:
        event_date = m.get("actual_date") or m.get("expected_date")
        if event_date:
            date_str = event_date.isoformat()
            if date_str not in events_by_date:
                events_by_date[date_str] = []

            events_by_date[date_str].append({
                "milestone_id": m["id"],
                "project_id": m["project_id"],
                "work_order_number": m.get("work_order_number"),
                "stage": m["stage"],
                "stage_label": m["stage"].replace("_", " ").title(),
                "priority": m.get("priority"),
                "is_complete": m.get("actual_date") is not None,
                "is_overdue": m.get("is_overdue", False)
            })

    return jsonify({
        "data": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "view": view,
            "events": events_by_date
        }
    })
