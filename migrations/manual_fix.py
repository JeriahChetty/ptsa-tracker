"""
Manual database fix script for adding order_index to AssignmentStep.
This is needed because SQLite doesn't support adding NOT NULL columns without defaults.

Run this script with Flask's app context:
$ flask shell
>>> from migrations.manual_fix import fix_assignment_steps
>>> fix_assignment_steps()
"""

def fix_assignment_steps():
    from app.extensions import db
    from app.models import AssignmentStep
    from sqlalchemy import text
    
    # Check if column exists
    try:
        db.session.execute(text("SELECT order_index FROM assignment_step LIMIT 1"))
        column_exists = True
    except Exception:
        column_exists = False

    # Add column if it doesn't exist
    if not column_exists:
        db.session.execute(text("ALTER TABLE assignment_step ADD COLUMN order_index INTEGER"))
        
    # Update all rows to have a valid order_index 
    assignments = {}
    for step in AssignmentStep.query.all():
        assignment_id = step.assignment_id
        if assignment_id not in assignments:
            assignments[assignment_id] = []
        assignments[assignment_id].append(step)
    
    # Sort steps by ID (default order) and assign order_index
    for assignment_id, steps in assignments.items():
        for index, step in enumerate(sorted(steps, key=lambda s: s.id)):
            step.order_index = index
            
    db.session.commit()
    print(f"Updated {sum(len(steps) for steps in assignments.values())} steps with order_index values")
    
    return True

if __name__ == "__main__":
    print("This script should be run from the Flask shell.")
    print("$ flask shell")
    print(">>> from migrations.manual_fix import fix_assignment_steps")
    print(">>> fix_assignment_steps()")
