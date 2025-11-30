"""Update target_completion_date for projects missing it."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db

def update_target_dates():
    """Set target_completion_date for projects that don't have one."""
    app = create_app()
    with app.app_context():
        # Update projects with NULL target_completion_date
        # Set it to 90 days after authorized_date
        query = f"""
            UPDATE {db.table_name('projects')}
            SET target_completion_date = DATE_ADD(authorized_date, 90)
            WHERE target_completion_date IS NULL
              AND authorized_date IS NOT NULL
        """
        affected = db.execute_write(query)
        print(f"Updated {affected} projects with target_completion_date")

        # Verify the update
        check_query = f"""
            SELECT COUNT(*) as with_target,
                   (SELECT COUNT(*) FROM {db.table_name('projects')}) as total
            FROM {db.table_name('projects')}
            WHERE target_completion_date IS NOT NULL
        """
        result = db.execute(check_query)
        if result:
            print(f"Projects with target_completion_date: {result[0]['with_target']}/{result[0]['total']}")

if __name__ == "__main__":
    update_target_dates()
