# STATUS_CHANGE Audit Log Data - Implementation Summary

## Overview
Successfully added mock STATUS_CHANGE audit log entries to the GPC Reliability database to demonstrate the multi-segment timeline feature.

## Execution Details

### Script Location
`/Users/rkalluri/projects/gpc_reliability/scripts/add_timeline_status_changes.py`

### Execution Date
2025-12-08

## Results Summary

### Projects Updated: 15

**Status Distribution:**
- `qa_qc`: 6 projects (3 transitions each)
- `approved`: 5 projects (4 transitions each)
- `construction_ready`: 4 projects (5 transitions each)

### STATUS_CHANGE Records Added: 58

**Breakdown:**
- 6 projects with 3 transitions = 18 records
- 5 projects with 4 transitions = 20 records
- 4 projects with 5 transitions = 20 records
- **Total: 58 STATUS_CHANGE audit log entries**

### Projects with Timeline Data

| Work Order | Current Status | Transitions | First Transition | Last Transition |
|------------|----------------|-------------|------------------|-----------------|
| WO-20240040 | qa_qc | 3 | 2025-11-18 | 2025-12-12 |
| WO-20240060 | approved | 4 | 2025-11-19 | 2025-12-25 |
| WO-20240065 | approved | 4 | 2025-11-15 | 2025-12-21 |
| WO-20240124 | approved | 4 | 2025-11-15 | 2025-12-21 |
| WO-20240140 | construction_ready | 5 | 2025-11-19 | 2026-01-06 |
| WO-20240353 | construction_ready | 5 | 2025-11-16 | 2026-01-03 |
| WO-20240354 | construction_ready | 5 | 2025-11-15 | 2026-01-02 |
| WO-20240369 | construction_ready | 5 | 2025-11-15 | 2026-01-02 |
| WO-20240394 | qa_qc | 3 | 2025-11-15 | 2025-12-09 |
| WO-20240439 | qa_qc | 3 | 2025-11-15 | 2025-12-09 |
| WO-20240489 | approved | 4 | 2025-11-17 | 2025-12-23 |
| WO-20240556 | approved | 4 | 2025-11-16 | 2025-12-22 |
| WO-20240624 | qa_qc | 3 | 2025-11-15 | 2025-12-09 |
| WO-20240637 | qa_qc | 3 | 2025-11-19 | 2025-12-13 |
| WO-20240676 | qa_qc | 3 | 2025-11-19 | 2025-12-13 |

## Sample Project: Full Status History

**Project: WO-20240140** (Current Status: `construction_ready`)

```
Status Progression Timeline:
=================================================
1. authorized → assigned_to_vendor
   Date: 2025-11-19
   User: project.manager@gpc.com

2. assigned_to_vendor → design_submitted
   Date: 2025-12-01
   User: qa.reviewer@gpc.com

3. design_submitted → qa_qc
   Date: 2025-12-13
   User: engineering@gpc.com

4. qa_qc → approved
   Date: 2025-12-25
   User: construction@gpc.com

5. approved → construction_ready
   Date: 2026-01-06
   User: lance.burton@gpc.com
```

**Timeline Duration:** 48 days (Nov 19, 2025 - Jan 6, 2026)
**Average Days per Stage:** ~12 days

## Data Characteristics

### Realistic Status Progression
- All projects follow the standard progression: `authorized` → `assigned_to_vendor` → `design_submitted` → `qa_qc` → `approved` → `construction_ready`
- Each transition has a 12-day interval between status changes
- Based on the project's authorized_date from the database

### User Diversity
Five different users rotate through the status changes:
- lance.burton@gpc.com
- project.manager@gpc.com
- qa.reviewer@gpc.com
- engineering@gpc.com
- construction@gpc.com

### Date Range
- Earliest transition: 2025-11-15
- Latest transition: 2026-01-06
- Total span: ~52 days

## Verification Instructions

### 1. Verify Record Count
```sql
SELECT COUNT(*) as count
FROM main.gpc_reliability.audit_logs
WHERE action = 'STATUS_CHANGE';
```
**Expected Result:** 58

### 2. View All Projects with Status History
```sql
SELECT
    p.work_order_number,
    p.status as current_status,
    COUNT(*) as transition_count
FROM main.gpc_reliability.audit_logs al
JOIN main.gpc_reliability.projects p ON al.project_id = p.id
WHERE al.action = 'STATUS_CHANGE'
GROUP BY p.work_order_number, p.status
ORDER BY p.work_order_number;
```
**Expected Result:** 15 rows

### 3. View Full History for a Specific Project
```sql
SELECT
    p.work_order_number,
    al.old_value,
    al.new_value,
    al.created_at,
    al.user_email
FROM main.gpc_reliability.audit_logs al
JOIN main.gpc_reliability.projects p ON al.project_id = p.id
WHERE al.action = 'STATUS_CHANGE'
    AND p.work_order_number = 'WO-20240140'
ORDER BY al.created_at;
```
**Expected Result:** 5 transitions

### 4. Test Backend API (Timeline Feature)

**Start the backend:**
```bash
cd /Users/rkalluri/projects/gpc_reliability
python wsgi.py
```

**Test specific project:**
```bash
curl http://127.0.0.1:5001/api/v1/gantt?work_order=WO-20240140 | python3 -m json.tool
```

**Expected Response Structure:**
```json
{
  "data": [
    {
      "work_order_number": "WO-20240140",
      "status": "construction_ready",
      "status_periods": [
        {
          "status": "authorized",
          "start_date": "2025-11-07",
          "end_date": "2025-11-19"
        },
        {
          "status": "assigned_to_vendor",
          "start_date": "2025-11-19",
          "end_date": "2025-12-01"
        },
        {
          "status": "design_submitted",
          "start_date": "2025-12-01",
          "end_date": "2025-12-13"
        },
        {
          "status": "qa_qc",
          "start_date": "2025-12-13",
          "end_date": "2025-12-25"
        },
        {
          "status": "approved",
          "start_date": "2025-12-25",
          "end_date": "2026-01-06"
        },
        {
          "status": "construction_ready",
          "start_date": "2026-01-06",
          "end_date": null
        }
      ]
    }
  ]
}
```

### 5. View Timeline in Frontend
1. Start the backend: `python wsgi.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to the Dashboard
4. View any of the 15 projects with status history
5. The timeline should show multiple colored segments representing different statuses

## Implementation Details

### Database Schema
```sql
Table: main.gpc_reliability.audit_logs
Columns:
  - id: STRING (UUID)
  - project_id: STRING (FK to projects)
  - action: STRING ('STATUS_CHANGE')
  - field_name: STRING ('status')
  - old_value: STRING (previous status)
  - new_value: STRING (new status)
  - changes: STRING (JSON: {"status": ["old", "new"]})
  - user_id: STRING
  - user_email: STRING
  - created_at: TIMESTAMP (when status changed)
```

### Status Stages (in order)
1. `authorized`
2. `assigned_to_vendor`
3. `design_submitted`
4. `qa_qc`
5. `approved`
6. `construction_ready`

### Transition Logic
- Each project has N-1 transitions, where N = current status index + 1
- `qa_qc` projects (index 3) have 3 transitions
- `approved` projects (index 4) have 4 transitions
- `construction_ready` projects (index 5) have 5 transitions

### Script Execution
The script uses the Databricks CLI to execute batch SQL inserts:
- Fetches 15 projects with advanced statuses
- Generates status transition records for each project
- Inserts records in batches of 50
- Verifies data integrity after insertion

## Success Criteria Verification

- ✅ **Add STATUS_CHANGE records for 10-15 projects:** Completed for 15 projects
- ✅ **Each project should have N-1 transitions:** Verified (3-5 transitions per project)
- ✅ **Verify record count:** 58 records added successfully
- ✅ **Should see 50-75 new STATUS_CHANGE records:** 58 records (within range)
- ✅ **Realistic date intervals:** 12-day intervals between transitions
- ✅ **Based on authorized_date:** All transitions calculated from project's authorized_date

## Next Steps

1. **Test the API:** Start the backend and verify the `status_periods` field is populated correctly
2. **Test the Frontend:** Verify the multi-segment timeline visualization displays correctly
3. **Add More Projects (Optional):** Run the script again to add more projects if needed
4. **Production Data:** Adapt this script pattern for production data population

## Files Created/Modified

### Created
- `/Users/rkalluri/projects/gpc_reliability/scripts/add_timeline_status_changes.py` - Main script for adding STATUS_CHANGE records
- `/Users/rkalluri/projects/gpc_reliability/STATUS_CHANGE_DATA_SUMMARY.md` - This summary document

### Database Tables Modified
- `main.gpc_reliability.audit_logs` - Added 58 new STATUS_CHANGE records

## Troubleshooting

### If you need to clear and re-run:
```sql
-- Remove all STATUS_CHANGE records
DELETE FROM main.gpc_reliability.audit_logs
WHERE action = 'STATUS_CHANGE';

-- Then re-run the script
python3 scripts/add_timeline_status_changes.py
```

### If you need to add more projects:
```python
# Modify the LIMIT in get_projects_for_timeline()
sql = f"""
    SELECT id, work_order_number, status, authorized_date
    FROM {table_name('projects')}
    WHERE status IN ('qa_qc', 'approved', 'construction_ready')
    ORDER BY authorized_date DESC
    LIMIT 30  -- Change this number
"""
```

## Contact
For questions or issues, contact: lance.burton@gpc.com
