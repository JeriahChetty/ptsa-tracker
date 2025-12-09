"""
Remove company-specific fields from measures table.

These fields (responsible, participants, departments, start_date, end_date) 
should only exist in the measure_assignments table where they are company-specific.
This prevents the confusion where editing a measure template affects all companies.

Run this migration with:
    python migrations/remove_measure_company_fields.py
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def upgrade():
    """Remove company-specific fields from measures table."""
    print("Removing company-specific fields from measures table...")
    
    app = create_app()
    with app.app_context():
        try:
            # Check if columns exist before trying to drop them
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('measures')]
            
            columns_to_drop = ['responsible', 'participants', 'departments', 'start_date', 'end_date']
            
            for column in columns_to_drop:
                if column in existing_columns:
                    print(f"Dropping column: {column}")
                    with db.engine.connect() as conn:
                        conn.execute(text(f'ALTER TABLE measures DROP COLUMN {column}'))
                        conn.commit()
                    print(f"✓ Dropped {column}")
                else:
                    print(f"⊘ Column {column} does not exist, skipping")
            
            print("\n✓ Migration completed successfully!")
            print("The measures table no longer has company-specific fields.")
            print("These details are now only stored in measure_assignments.")
            
        except Exception as e:
            print(f"\n✗ Error during migration: {str(e)}")
            db.session.rollback()
            raise

def downgrade():
    """Re-add company-specific fields to measures table."""
    print("WARNING: This will re-add fields that should not be used.")
    print("These fields should only exist in measure_assignments table.")
    
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE measures ADD COLUMN responsible VARCHAR(255)'))
                conn.execute(text('ALTER TABLE measures ADD COLUMN participants VARCHAR(255)'))
                conn.execute(text('ALTER TABLE measures ADD COLUMN departments VARCHAR(255)'))
                conn.execute(text('ALTER TABLE measures ADD COLUMN start_date DATE'))
                conn.execute(text('ALTER TABLE measures ADD COLUMN end_date DATE'))
                conn.commit()
            
            print("✓ Downgrade completed (fields re-added)")
            
        except Exception as e:
            print(f"✗ Error during downgrade: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
