"""
Manual fix for the database to add order_index column to assignment_step table.
This bypasses the Alembic migration to work around SQLite limitations.
"""
import os
import sys
import sqlite3
from pathlib import Path

def get_db_path():
    base_dir = Path(__file__).resolve().parent.parent
    instance_dir = base_dir / 'instance'
    db_path = instance_dir / 'app.db'
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return None
    
    return str(db_path)

def fix_database():
    db_path = get_db_path()
    if not db_path:
        return False
        
    print(f"Working with database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(assignment_step)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'order_index' not in columns:
            print("Adding order_index column to assignment_step table...")
            
            # Add the column as nullable initially
            cursor.execute("ALTER TABLE assignment_step ADD COLUMN order_index INTEGER")
            
            # Update existing rows with sequential values grouped by assignment_id
            cursor.execute("""
                WITH indexed_steps AS (
                    SELECT id, assignment_id, 
                           ROW_NUMBER() OVER (PARTITION BY assignment_id ORDER BY id) - 1 as row_idx
                    FROM assignment_step
                )
                UPDATE assignment_step
                SET order_index = (
                    SELECT row_idx FROM indexed_steps 
                    WHERE indexed_steps.id = assignment_step.id
                )
            """)
            
            print("Column added and existing rows updated successfully!")
        else:
            print("Column 'order_index' already exists in assignment_step table.")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_database()
    sys.exit(0 if success else 1)
