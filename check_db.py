"""
Script to check database integrity and relationships
"""
from app import create_app
from app.extensions import db
from app.models import Measure, MeasureAssignment, MeasureStep

def check_db():
    """Check database tables and constraints."""
    app = create_app()
    
    with app.app_context():
        print("==== Checking Database ====")
        print("\n== Measures ==")
        measures = Measure.query.all()
        print(f"Total measures: {len(measures)}")
        
        for m in measures:
            print(f"- Measure ID {m.id}: {m.name}")
            print(f"  Assignments: {len(m.assignments)}")
            print(f"  Steps: {len(m.steps)}")
        
        print("\n== Database Tables ==")
        inspector = db.inspect(db.engine)
        for table_name in inspector.get_table_names():
            print(f"Table: {table_name}")
            for column in inspector.get_columns(table_name):
                print(f"  - {column['name']}: {column['type']}")
            
            print("  Foreign Keys:")
            for fk in inspector.get_foreign_keys(table_name):
                print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                print(f"      ondelete: {fk.get('options', {}).get('ondelete', 'unknown')}")

if __name__ == "__main__":
    check_db()
