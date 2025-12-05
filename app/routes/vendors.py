"""Vendors API endpoints."""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from app.database import db
from app.models.vendor import Vendor

vendors_bp = Blueprint("vendors", __name__)


def table_name(table: str) -> str:
    return db.table_name(table)


@vendors_bp.route("", methods=["GET"])
def list_vendors():
    """List all vendors with optional filtering and metrics.

    Query params:
        - active_only: Filter to only active vendors (default: false)
        - search: Search in name and code
        - sort_by: Sort field (default: name)
        - sort_order: asc or desc (default: asc)
    """
    conditions = []

    # Active filter
    active_only = request.args.get("active_only", "false").lower() == "true"
    if active_only:
        conditions.append("v.is_active = true")

    # Search filter
    search = request.args.get("search")
    if search:
        search_escaped = search.replace("'", "''")
        conditions.append(f"(v.name LIKE '%{search_escaped}%' OR v.code LIKE '%{search_escaped}%')")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Sorting
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "ASC"

    valid_sort_fields = ["name", "code", "created_at", "updated_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "name"

    # Query vendors with project stats and metrics (current and previous for trend)
    query = f"""
        SELECT
            v.*,
            COALESCE(ps.total_projects, 0) as total_projects,
            COALESCE(ps.active_projects, 0) as active_projects,
            COALESCE(ps.completed_projects, 0) as completed_projects,
            vm_current.on_time_rate as on_time_percentage,
            vm_prev.on_time_rate as prev_on_time_percentage
        FROM {table_name('vendors')} v
        LEFT JOIN (
            SELECT
                vendor_id,
                COUNT(*) as total_projects,
                SUM(CASE WHEN status != 'construction_ready' THEN 1 ELSE 0 END) as active_projects,
                SUM(CASE WHEN status = 'construction_ready' THEN 1 ELSE 0 END) as completed_projects
            FROM {table_name('projects')}
            GROUP BY vendor_id
        ) ps ON v.id = ps.vendor_id
        LEFT JOIN (
            SELECT vendor_id, on_time_rate,
                   ROW_NUMBER() OVER (PARTITION BY vendor_id ORDER BY period_end DESC) as rn
            FROM {table_name('vendor_metrics')}
        ) vm_current ON v.id = vm_current.vendor_id AND vm_current.rn = 1
        LEFT JOIN (
            SELECT vendor_id, on_time_rate,
                   ROW_NUMBER() OVER (PARTITION BY vendor_id ORDER BY period_end DESC) as rn
            FROM {table_name('vendor_metrics')}
        ) vm_prev ON v.id = vm_prev.vendor_id AND vm_prev.rn = 2
        WHERE {where_clause}
        ORDER BY v.{sort_by} {sort_order}
    """
    rows = db.execute(query)

    vendors = []
    for row in rows:
        vendor = Vendor.from_row(row).to_dict()
        # Add computed fields
        vendor["total_projects"] = row.get("total_projects", 0)
        vendor["active_projects"] = row.get("active_projects", 0)
        vendor["completed_projects"] = row.get("completed_projects", 0)
        current_rate = row.get("on_time_percentage") or 0
        prev_rate = row.get("prev_on_time_percentage")
        vendor["on_time_percentage"] = round(current_rate, 1)
        # Calculate trend: 'up', 'down', or 'stable' (null if no previous data)
        if prev_rate is not None:
            if current_rate > prev_rate + 1:
                vendor["on_time_trend"] = "up"
            elif current_rate < prev_rate - 1:
                vendor["on_time_trend"] = "down"
            else:
                vendor["on_time_trend"] = "stable"
        else:
            vendor["on_time_trend"] = None
        vendors.append(vendor)

    return jsonify({
        "data": vendors,
        "total": len(vendors)
    })


@vendors_bp.route("/<vendor_id>", methods=["GET"])
def get_vendor(vendor_id):
    """Get vendor details by ID with project statistics."""
    query = f"SELECT * FROM {table_name('vendors')} WHERE id = '{vendor_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Vendor not found"}), 404

    vendor = Vendor.from_row(rows[0])
    vendor_dict = vendor.to_dict()

    # Get project statistics for this vendor
    stats_query = f"""
        SELECT
            COUNT(*) as total_projects,
            SUM(CASE WHEN status = 'construction_ready' THEN 1 ELSE 0 END) as completed_projects,
            SUM(CASE WHEN status != 'construction_ready' THEN 1 ELSE 0 END) as active_projects
        FROM {table_name('projects')}
        WHERE vendor_id = '{vendor_id}'
    """
    stats = db.execute(stats_query)
    if stats:
        vendor_dict["project_stats"] = {
            "total": stats[0].get("total_projects", 0),
            "completed": stats[0].get("completed_projects", 0),
            "active": stats[0].get("active_projects", 0)
        }

    return jsonify({"data": vendor_dict})


@vendors_bp.route("", methods=["POST"])
def create_vendor():
    """Create a new vendor."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Map frontend field names to backend field names
    if "vendor_name" in data and "name" not in data:
        data["name"] = data["vendor_name"]

    # Generate code from name if not provided
    if "name" in data and "code" not in data:
        # Create a code from the name (first 6 chars uppercase, no spaces)
        data["code"] = data["name"].upper().replace(" ", "")[:6]

    # Validate required fields
    required = ["name", "code"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Check if code already exists
    check_query = f"SELECT id FROM {table_name('vendors')} WHERE code = '{data['code']}'"
    existing = db.execute(check_query)
    if existing:
        return jsonify({"error": "Vendor code already exists"}), 409

    # Create vendor
    vendor_id = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    name = data["name"].replace("'", "''")
    code = data["code"].replace("'", "''")
    contact_name = (data.get("contact_name") or "").replace("'", "''")
    contact_email = (data.get("contact_email") or "").replace("'", "''")
    is_active = str(data.get("is_active", True)).lower()

    insert_query = f"""
        INSERT INTO {table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES ('{vendor_id}', '{name}', '{code}', '{contact_name}', '{contact_email}',
                {is_active}, '{now}', '{now}')
    """
    db.execute_write(insert_query)

    return get_vendor(vendor_id)


@vendors_bp.route("/<vendor_id>", methods=["PATCH"])
def update_vendor(vendor_id):
    """Update vendor details."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Map frontend field names to backend field names
    if "vendor_name" in data:
        data["name"] = data["vendor_name"]

    # Check if vendor exists
    query = f"SELECT * FROM {table_name('vendors')} WHERE id = '{vendor_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Vendor not found"}), 404

    # Build UPDATE statement
    updates = []
    updatable_fields = ["name", "code", "contact_name", "contact_email", "is_active"]

    for field in updatable_fields:
        if field in data:
            new_value = data[field]
            if field == "is_active":
                updates.append(f"{field} = {str(new_value).lower()}")
            elif new_value is None:
                updates.append(f"{field} = NULL")
            else:
                updates.append(f"{field} = '{str(new_value).replace(chr(39), chr(39)+chr(39))}'")

    if not updates:
        return jsonify({"message": "No changes to apply"}), 200

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    updates.append(f"updated_at = '{now}'")

    update_query = f"""
        UPDATE {table_name('vendors')}
        SET {', '.join(updates)}
        WHERE id = '{vendor_id}'
    """
    db.execute_write(update_query)

    return get_vendor(vendor_id)


@vendors_bp.route("/<vendor_id>", methods=["DELETE"])
def delete_vendor(vendor_id):
    """Delete a vendor (only if no associated projects)."""
    # Check if vendor exists
    query = f"SELECT id FROM {table_name('vendors')} WHERE id = '{vendor_id}'"
    rows = db.execute(query)

    if not rows:
        return jsonify({"error": "Vendor not found"}), 404

    # Check for associated projects
    projects_query = f"SELECT COUNT(*) as count FROM {table_name('projects')} WHERE vendor_id = '{vendor_id}'"
    projects = db.execute(projects_query)
    if projects and projects[0].get("count", 0) > 0:
        return jsonify({
            "error": "Cannot delete vendor with associated projects",
            "project_count": projects[0]["count"]
        }), 409

    # Delete vendor metrics first
    db.execute_write(f"DELETE FROM {table_name('vendor_metrics')} WHERE vendor_id = '{vendor_id}'")

    # Delete vendor
    db.execute_write(f"DELETE FROM {table_name('vendors')} WHERE id = '{vendor_id}'")

    return jsonify({"message": "Vendor deleted successfully"})


@vendors_bp.route("/<vendor_id>/metrics", methods=["GET"])
def get_vendor_metrics(vendor_id):
    """Get vendor performance metrics."""
    # Check if vendor exists
    vendor_query = f"SELECT id, name FROM {table_name('vendors')} WHERE id = '{vendor_id}'"
    vendor_rows = db.execute(vendor_query)

    if not vendor_rows:
        return jsonify({"error": "Vendor not found"}), 404

    # Get stored metrics
    metrics_query = f"""
        SELECT * FROM {table_name('vendor_metrics')}
        WHERE vendor_id = '{vendor_id}'
        ORDER BY period_end DESC
        LIMIT 1
    """
    metrics_rows = db.execute(metrics_query)

    if not metrics_rows:
        # Calculate metrics on the fly if none stored
        calc_query = f"""
            SELECT
                COUNT(*) as total_projects,
                SUM(CASE WHEN status = 'construction_ready' THEN 1 ELSE 0 END) as completed_projects,
                SUM(CASE WHEN status != 'construction_ready' THEN 1 ELSE 0 END) as active_projects,
                AVG(revision_count) as avg_revisions
            FROM {table_name('projects')}
            WHERE vendor_id = '{vendor_id}'
        """
        calc_result = db.execute(calc_query)

        if calc_result:
            row = calc_result[0]
            return jsonify({
                "data": {
                    "vendor_id": vendor_id,
                    "vendor_name": vendor_rows[0].get("name"),
                    "total_projects": row.get("total_projects", 0),
                    "completed_projects": row.get("completed_projects", 0),
                    "active_projects": row.get("active_projects", 0),
                    "avg_revisions": round(row.get("avg_revisions", 0) or 0, 2),
                    "calculated": True
                }
            })

        return jsonify({"data": None})

    row = metrics_rows[0]
    return jsonify({
        "data": {
            "id": row["id"],
            "vendor_id": row["vendor_id"],
            "vendor_name": vendor_rows[0].get("name"),
            "period_start": row["period_start"].isoformat() if row.get("period_start") else None,
            "period_end": row["period_end"].isoformat() if row.get("period_end") else None,
            "total_projects": row.get("total_projects"),
            "completed_projects": row.get("completed_projects"),
            "active_projects": row.get("active_projects"),
            "overdue_projects": row.get("overdue_projects"),
            "on_time_rate": row.get("on_time_rate"),
            "avg_cycle_time_days": row.get("avg_cycle_time_days"),
            "revision_rate": row.get("revision_rate"),
            "sla_compliance_rate": row.get("sla_compliance_rate"),
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        }
    })


@vendors_bp.route("/<vendor_id>/projects", methods=["GET"])
def get_vendor_projects(vendor_id):
    """Get all projects for a specific vendor."""
    # Check if vendor exists
    vendor_query = f"SELECT id FROM {table_name('vendors')} WHERE id = '{vendor_id}'"
    if not db.execute(vendor_query):
        return jsonify({"error": "Vendor not found"}), 404

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
    offset = (page - 1) * per_page

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM {table_name('projects')} WHERE vendor_id = '{vendor_id}'"
    count_result = db.execute(count_query)
    total = count_result[0]["total"] if count_result else 0

    # Get projects
    query = f"""
        SELECT * FROM {table_name('projects')}
        WHERE vendor_id = '{vendor_id}'
        ORDER BY created_at DESC
        LIMIT {per_page} OFFSET {offset}
    """
    rows = db.execute(query)

    projects = []
    for row in rows:
        projects.append({
            "id": row["id"],
            "work_order_number": row["work_order_number"],
            "description": row.get("description"),
            "region": row.get("region"),
            "status": row["status"],
            "priority": row["priority"],
            "authorized_date": row["authorized_date"].isoformat() if row.get("authorized_date") else None,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None
        })

    return jsonify({
        "data": projects,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })


@vendors_bp.route("/admin/seed-inactive", methods=["POST"])
def seed_inactive_vendors():
    """Admin endpoint to add inactive vendors to the database."""
    from datetime import datetime

    # Inactive vendor data
    inactive_vendors = [
        {"name": "Legacy Power Solutions", "code": "LEGACY", "contact_name": "Tom Bradley", "contact_email": "tbradley@legacypower.com"},
        {"name": "Southern Grid Services", "code": "SGS", "contact_name": "Karen Mitchell", "contact_email": "kmitchell@southerngrid.com"},
        {"name": "Atlantic Electric Works", "code": "AEW", "contact_name": "Frank Rodriguez", "contact_email": "frodriguez@atlanticelectric.com"},
        {"name": "Peachtree Utility Contractors", "code": "PUC", "contact_name": "Nancy Cooper", "contact_email": "ncooper@peachtreeutility.com"},
        {"name": "Dixie Line Construction", "code": "DIXIE", "contact_name": "Bill Thompson", "contact_email": "bthompson@dixieline.com"},
    ]

    now = datetime.utcnow().isoformat()
    added = 0

    for data in inactive_vendors:
        # Check if vendor already exists
        check_query = f"SELECT id FROM {table_name('vendors')} WHERE code = '{data['code']}'"
        existing = db.execute(check_query)
        if existing:
            continue

        vendor_id = str(uuid.uuid4())
        query = f"""
        INSERT INTO {table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES ('{vendor_id}', '{data["name"]}', '{data["code"]}',
                '{data["contact_name"]}', '{data["contact_email"]}', false,
                '{now}', '{now}')
        """
        db.execute_write(query)
        added += 1

    return jsonify({
        "message": f"Added {added} inactive vendors",
        "total_inactive": len(inactive_vendors)
    })


@vendors_bp.route("/admin/seed-poor-performer", methods=["POST"])
def seed_poor_performer():
    """Admin endpoint to add a poor performing vendor with declining metrics."""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Check if vendor already exists
    check_query = f"SELECT id FROM {table_name('vendors')} WHERE code = 'BADCO'"
    existing = db.execute(check_query)

    if existing:
        vendor_id = existing[0]["id"]
    else:
        # Create poor performing vendor
        vendor_id = str(uuid.uuid4())
        vendor_query = f"""
        INSERT INTO {table_name('vendors')}
        (id, name, code, contact_name, contact_email, is_active, created_at, updated_at)
        VALUES ('{vendor_id}', 'Unreliable Contractors LLC', 'BADCO',
                'Bob Slacker', 'bslacker@unreliable.com', true,
                '{now_str}', '{now_str}')
        """
        db.execute_write(vendor_query)

    # Delete existing metrics for this vendor
    db.execute_write(f"DELETE FROM {table_name('vendor_metrics')} WHERE vendor_id = '{vendor_id}'")

    # Add two metric periods - showing a declining trend
    # Previous period: 65% on-time (not great but ok)
    prev_period_end = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    prev_period_start = (now - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    prev_metric_id = str(uuid.uuid4())

    prev_metrics_query = f"""
    INSERT INTO {table_name('vendor_metrics')}
    (id, vendor_id, period_start, period_end, total_projects, completed_projects,
     active_projects, overdue_projects, on_time_rate, avg_cycle_time_days,
     revision_rate, sla_compliance_rate, created_at, updated_at)
    VALUES ('{prev_metric_id}', '{vendor_id}', '{prev_period_start}', '{prev_period_end}',
            25, 10, 15, 8, 65.0, 45.5, 2.1, 70.0, '{now_str}', '{now_str}')
    """
    db.execute_write(prev_metrics_query)

    # Current period: 38% on-time (poor, declining)
    curr_period_end = now_str
    curr_period_start = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    curr_metric_id = str(uuid.uuid4())

    curr_metrics_query = f"""
    INSERT INTO {table_name('vendor_metrics')}
    (id, vendor_id, period_start, period_end, total_projects, completed_projects,
     active_projects, overdue_projects, on_time_rate, avg_cycle_time_days,
     revision_rate, sla_compliance_rate, created_at, updated_at)
    VALUES ('{curr_metric_id}', '{vendor_id}', '{curr_period_start}', '{curr_period_end}',
            30, 8, 22, 15, 38.5, 62.3, 3.2, 45.0, '{now_str}', '{now_str}')
    """
    db.execute_write(curr_metrics_query)

    return jsonify({
        "message": "Added poor performing vendor with declining metrics",
        "vendor_id": vendor_id,
        "vendor_name": "Unreliable Contractors LLC",
        "current_on_time": 38.5,
        "previous_on_time": 65.0,
        "trend": "down"
    })
