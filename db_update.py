import sqlite3
import os

def add_order_field_to_tables():
    # Get the database path from the environment or use default
    db_path = os.environ.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
    if not db_path:
        db_path = 'instance/ptsa.db'  # Default SQLite database location
    
    print(f"Using database at: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if 'order' column exists in the measures table
        cursor.execute("PRAGMA table_info(measures)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'order' not in column_names:
            print("Adding 'order' column to measures table...")
            cursor.execute("ALTER TABLE measures ADD COLUMN 'order' INTEGER DEFAULT 0")
            print("Column added successfully to measures table")
        else:
            print("'order' column already exists in measures table")
        
        # Check if steps table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='steps'")
        if not cursor.fetchone():
            print("Creating steps table...")
            cursor.execute('''
                CREATE TABLE steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measure_id INTEGER NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    "order" INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(measure_id) REFERENCES measures(id)
                )
            ''')
            print("Steps table created successfully")
        else:
            # Check if 'order' column exists in the steps table
            cursor.execute("PRAGMA table_info(steps)")
            step_columns = cursor.fetchall()
            step_column_names = [col[1] for col in step_columns]
            
            if 'order' not in step_column_names:
                print("Adding 'order' column to steps table...")
                cursor.execute("ALTER TABLE steps ADD COLUMN 'order' INTEGER DEFAULT 0")
                print("Column added successfully to steps table")
            else:
                print("'order' column already exists in steps table")
        
        conn.commit()
        print("Database updated successfully!")
        
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_order_field_to_tables()
