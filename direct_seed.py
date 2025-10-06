import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def get_db_path():
    """Get the SQLite database path from environment or use default."""
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/ptsa.db')
    if db_uri.startswith('sqlite:///'):
        return db_uri[10:]  # Remove the sqlite:/// prefix
    return 'instance/ptsa.db'  # Default location

def execute_query(cursor, query, params=None):
    """Execute a SQL query with error handling."""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return True
    except sqlite3.Error as e:
        print(f"SQL Error: {e}")
        return False

def seed_admin(conn, cursor):
    """Seed admin user."""
    print("Seeding admin user...")
    
    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@ptsa.com'")
    if cursor.fetchone():
        print("Admin user already exists")
        return
    
    # Hash password
    password_hash = generate_password_hash("Admin123!")
    
    # Insert admin user
    execute_query(cursor, """
        INSERT INTO users (email, password_hash, name, role, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, ('admin@ptsa.com', password_hash, 'Administrator', 'admin', 1))
    
    print("Admin user created successfully")

def seed_companies(conn, cursor):
    """Seed company data."""
    print("Seeding companies...")
    
    companies = [
        ('Acme Tooling', 'Gauteng', 'Automotive', 'John Smith', '555-1234', 
         'contact@acmetooling.com', '123 Industry Way'),
        ('Bravo Plastics', 'KwaZulu-Natal', 'Plastics', 'Jane Doe', '555-5678', 
         'info@bravoplastics.com', '456 Manufacturing Blvd'),
        ('Cobalt Engineering', 'Western Cape', 'General Engineering', 'Sam Johnson', 
         '555-9012', 'hello@cobalteng.com', '789 Engineering Road'),
    ]
    
    for company in companies:
        name = company[0]
        cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
        if cursor.fetchone():
            print(f"Company {name} already exists")
            continue
            
        execute_query(cursor, """
            INSERT INTO companies (name, region, industry_category, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, company)
        
        print(f"Company {name} created successfully")

def seed_measures(conn, cursor):
    """Seed measure data with order fields."""
    print("Seeding measures...")
    
    # Check if 'order' column exists in measures table
    cursor.execute("PRAGMA table_info(measures)")
    columns = [col[1] for col in cursor.fetchall()]
    
    has_order = 'order' in columns
    has_title = 'title' in columns
    name_field = 'title' if has_title else 'name'
    
    measures = [
        ('5S Implementation', 'Roll out 5S across the machining area.', 0),
        ('Preventive Maintenance Program', 'Establish and execute PM schedule for critical machines.', 1),
        ('Incoming Quality Inspection', 'Set up incoming inspection for key purchased components.', 2),
    ]
    
    for measure in measures:
        name = measure[0]
        cursor.execute(f"SELECT id FROM measures WHERE {name_field} = ?", (name,))
        measure_id = cursor.fetchone()
        
        if measure_id:
            measure_id = measure_id[0]
            if has_order:
                execute_query(cursor, f"""
                    UPDATE measures SET "order" = ? WHERE id = ?
                """, (measure[2], measure_id))
                print(f"Updated measure {name} order to {measure[2]}")
        else:
            if has_order:
                execute_query(cursor, f"""
                    INSERT INTO measures ({name_field}, description, "order")
                    VALUES (?, ?, ?)
                """, measure)
            else:
                execute_query(cursor, f"""
                    INSERT INTO measures ({name_field}, description)
                    VALUES (?, ?)
                """, measure[:2])
            print(f"Created measure {name}")

def main():
    """Main function to seed the database."""
    db_path = get_db_path()
    print(f"Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Seed data
        seed_admin(conn, cursor)
        seed_companies(conn, cursor)
        seed_measures(conn, cursor)
        
        # Commit changes
        conn.commit()
        print("Database seeding completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    main()
