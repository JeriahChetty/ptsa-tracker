#!/usr/bin/env python3
"""
Database inspection and table creation script
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def find_database():
    """Find the SQLite database file by checking common locations"""
    possible_locations = [
        Path('instance/app.db'),
        Path('instance/ptsa_tracker.db'),
        Path('instance/site.db'),
        Path('app.db'),
        Path('ptsa_tracker.db'),
        Path('app/app.db')
    ]
    
    # Check additional locations
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db') and 'venv' not in root:
                possible_locations.append(Path(os.path.join(root, file)))
    
    for location in possible_locations:
        if location.exists():
            print(f"Found database at: {location}")
            return location
    
    print("Database not found in common locations.")
    user_path = input("Please enter the path to your database file: ")
    path = Path(user_path)
    if path.exists():
        return path
    else:
        print(f"File not found: {user_path}")
        return None

def fix_database():
    """Add order_index column to assignment_step table"""
    db_path = find_database()
    if not db_path:
        return False
    
    print(f"Working with database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the assignment_step table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assignment_step'")
        if not cursor.fetchone():
            print("Table 'assignment_step' not found. Checking alternate names...")
            
            # Try with a different name
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%assignment%' AND name LIKE '%step%')")
            table = cursor.fetchone()
            if table:
                table_name = table[0]
                print(f"Found similar table: {table_name}")
            else:
                print("No assignment step table found.")
                return False
        else:
            table_name = 'assignment_step'
        
        # Check if order_index column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'order_index' not in columns:
            print(f"Adding order_index column to {table_name}...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN order_index INTEGER")
            
            # Update existing steps with sequential order based on assignment_id
            print("Updating existing steps with order values...")
            cursor.execute(f"""
                WITH indexed AS (
                    SELECT 
                        id, 
                        assignment_id,
                        ROW_NUMBER() OVER (PARTITION BY assignment_id ORDER BY id) - 1 as row_num
                    FROM {table_name}
                )
                UPDATE {table_name}
                SET order_index = (
                    SELECT row_num 
                    FROM indexed 
                    WHERE indexed.id = {table_name}.id
                )
            """)
            
            # Get count of updated rows
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE order_index IS NOT NULL")
            count = cursor.fetchone()[0]
            
            print(f"✓ Added column and updated {count} rows with order values")
            conn.commit()
            return True
        else:
            print("Column 'order_index' already exists in the table.")
            return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {str(e)}")
        return False
    
    finally:
        conn.close()

def inspect_and_fix_database():
    """Inspect existing database structure and fix issues"""
    
    print("🔍 PTSA Tracker - Database Inspector")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from sqlalchemy import inspect, text
        
        app = create_app()
        
        with app.app_context():
            # Check existing tables
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📊 Found {len(existing_tables)} existing tables:")
            for table in sorted(existing_tables):
                print(f"  ✅ {table}")
            
            # Check if company table exists (might be named differently)
            company_tables = [t for t in existing_tables if 'company' in t.lower() or 'companies' in t.lower()]
            
            if company_tables:
                print(f"\n🏢 Company-related tables found:")
                for table in company_tables:
                    print(f"  📋 {table}")
                    
                    # Show columns for company table
                    columns = inspector.get_columns(table)
                    print(f"    Columns: {', '.join([col['name'] for col in columns])}")
            else:
                print(f"\n❌ No company table found!")
                print("   Need to create the Company model first")
                return False
            
            # Try to import and check models
            print(f"\n🔧 Checking models...")
            try:
                from app.models import Company
                print(f"  ✅ Company model imported successfully")
                print(f"     Table name: {Company.__tablename__}")
                
                # Check if the table name matches
                if Company.__tablename__ not in existing_tables:
                    print(f"  ⚠️  Model table name '{Company.__tablename__}' doesn't match existing tables")
                    print(f"     Creating missing table...")
                    Company.__table__.create(db.engine, checkfirst=True)
                    print(f"  ✅ Company table created")
                
            except ImportError as e:
                print(f"  ❌ Cannot import Company model: {e}")
                return False
            
            # Now try Benchmarking model
            try:
                from app.models import Benchmarking
                print(f"  ✅ Benchmarking model imported successfully")
                print(f"     Table name: {Benchmarking.__tablename__}")
                
                # Create benchmarking table
                if Benchmarking.__tablename__ not in existing_tables:
                    print(f"  🏗️  Creating benchmarking table...")
                    Benchmarking.__table__.create(db.engine, checkfirst=True)
                    print(f"  ✅ Benchmarking table created")
                else:
                    print(f"  ✅ Benchmarking table already exists")
                
            except Exception as e:
                print(f"  ❌ Error with Benchmarking model: {e}")
                print(f"     Trying to create all tables...")
                
                # Try creating all tables
                db.create_all()
                print(f"  ✅ All tables created")
            
            # Final verification
            print(f"\n✅ Final verification...")
            inspector = inspect(db.engine)
            final_tables = inspector.get_table_names()
            
            required_tables = ['company', 'benchmarking']
            missing_tables = [t for t in required_tables if t not in final_tables]
            
            if missing_tables:
                print(f"  ❌ Still missing tables: {missing_tables}")
                return False
            else:
                print(f"  ✅ All required tables exist!")
                return True
                
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        return False

if __name__ == "__main__":
    if fix_database():
        print("\nDatabase updated successfully! You can now run your application.")
    else:
        print("\nFailed to update the database.")
    
    success = inspect_and_fix_database()
    
    if success:
        print(f"\n🎉 Database setup completed successfully!")
        print(f"✨ You can now run the benchmarking seed script")
    else:
        print(f"\n❌ Database setup failed. Check the errors above.")
        sys.exit(1)
