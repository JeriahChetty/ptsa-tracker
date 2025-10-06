"""
Manual fix script for adding order_index to AssignmentStep.
Run this script directly from the Flask shell.
"""
def fix_assignment_steps():
    """Add order_index column to assignment_step table and populate with values."""
    from app.extensions import db
    
    # Add column if needed (this will be nullable which is OK in SQLite)
    db.session.execute("PRAGMA foreign_keys=off;")
    try:
        db.session.execute("ALTER TABLE assignment_step ADD COLUMN order_index INTEGER;")
        db.session.commit()
        print("Added order_index column to assignment_step table")
    except Exception as e:
        db.session.rollback()
        print(f"Column may already exist: {e}")
    
    # Import this here to prevent circular imports
    from app.models import AssignmentStep, MeasureAssignment
    
    # Group steps by assignment_id and update order_index
    assignments = MeasureAssignment.query.all()
    update_count = 0
    
    for assignment in assignments:
        steps = AssignmentStep.query.filter_by(assignment_id=assignment.id).all()
        for i, step in enumerate(steps):
            step.order_index = i
            update_count += 1
    
    db.session.commit()
    print(f"Updated {update_count} steps with order_index values")
    
    # Re-enable foreign keys
    db.session.execute("PRAGMA foreign_keys=on;")
    
    return True

if __name__ == "__main__":
    fix_assignment_steps()
if __name__ == "__main__":
    fix_assignment_steps()
