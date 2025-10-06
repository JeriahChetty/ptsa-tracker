from app import create_app, db
from app.models import Measure, Step
from sqlalchemy import MetaData, Table, Column, Integer

app = create_app()

def run_manual_migration():
    with app.app_context():
        # Add order column to existing measures table
        engine = db.engine
        metadata = MetaData()
        metadata.bind = engine
        
        # Inspect existing measure table
        measure_table = Table('measures', metadata, autoload_with=engine)
        
        # Check if order column exists
        if 'order' not in measure_table.c:
            print("Adding 'order' column to measures table...")
            with engine.begin() as connection:
                connection.execute(db.text(
                    "ALTER TABLE measures ADD COLUMN order INTEGER DEFAULT 0"
                ))
            print("Column added successfully")
        else:
            print("'order' column already exists in measures table")
        
        # Create steps table if it doesn't exist
        if not engine.has_table('steps'):
            print("Creating steps table...")
            Step.__table__.create(engine)
            print("Steps table created successfully")
        else:
            print("Steps table already exists")

if __name__ == "__main__":
    run_manual_migration()
