"""
Script to seed database directly without using Flask CLI.
This avoids potential model relationship conflicts.
"""
import sqlite3
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash

def seed_database():
    # Get database path
    db_path = os.environ.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
    if not db_path:
        db_path = 'instance/ptsa.db'  # Default SQLite database location
    
    print(f"Using database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, inspect the users table to get column names
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Available columns in users table: {column_names}")
        
        # Determine password column name
        password_column = "password"
        if "password_hash" in column_names:
            password_column = "password_hash"
        
        # 1. Seed users table
        print(f"Seeding users table using '{password_column}' column...")
        hashed_password = generate_password_hash("Admin123!")
        
        # Use proper column name and check if user already exists
        cursor.execute(f"SELECT id FROM users WHERE email = 'admin@ptsa.com'")
        if cursor.fetchone():
            print("Admin user already exists")
        else:
            cursor.execute(f"""
                INSERT INTO users (email, {password_column}, name, role, is_active)
                VALUES ('admin@ptsa.com', ?, 'Administrator', 'admin', 1)
            """, (hashed_password,))
            print("Admin user created")
        
        # 2. Seed companies table
        print("Seeding companies table...")
        companies = [
            ('Acme Tooling', 'Gauteng', 'Automotive', 'John Smith', '555-1234', 'contact@acmetooling.com', '123 Industry Way'),
            ('Bravo Plastics', 'KwaZulu-Natal', 'Plastics', 'Jane Doe', '555-5678', 'info@bravoplastics.com', '456 Manufacturing Blvd')
        ]
        
        for company in companies:
            # Check if company already exists
            cursor.execute("SELECT id FROM companies WHERE name = ?", (company[0],))
            if cursor.fetchone():
                print(f"Company {company[0]} already exists")
            else:
                cursor.execute("""
                    INSERT INTO companies (name, region, industry_category, contact_person, phone, email, address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, company)
                print(f"Company {company[0]} created")
        
        # 3. Check if measures table has order column
        cursor.execute("PRAGMA table_info(measures)")
        measure_columns = [col[1] for col in cursor.fetchall()]
        has_order_column = "order" in measure_columns
        
        # 4. Seed measures table with order field if it exists
        print("Seeding measures table...")
        measures = [
            ('5S Implementation', 'Roll out 5S across the machining area.', 0),
            ('Preventive Maintenance Program', 'Establish and execute PM schedule for critical machines.', 1),
            ('Incoming Quality Inspection', 'Set up incoming inspection for key purchased components.', 2)
        ]
        
        for measure in measures:
            # Check if measure already exists
            cursor.execute("SELECT id FROM measures WHERE title = ?", (measure[0],))
            measure_id = cursor.fetchone()
            
            if measure_id:
                # Update order if the column exists
                if has_order_column:
                    cursor.execute("""
                        UPDATE measures SET "order" = ? WHERE id = ?
                    """, (measure[2], measure_id[0]))
                    print(f"Updated order for measure {measure[0]}")
            else:
                if has_order_column:
                    cursor.execute("""
                        INSERT INTO measures (title, description, "order") 
                        VALUES (?, ?, ?)
                    """, measure)
                else:
                    cursor.execute("""
                        INSERT INTO measures (title, description) 
                        VALUES (?, ?)
                    """, measure[:2])
                print(f"Created measure {measure[0]}")
            
        conn.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {str(e)}")
        print("Consider using python seed_data.py or python seed_admin.py instead")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
