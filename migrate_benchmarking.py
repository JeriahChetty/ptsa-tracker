#!/usr/bin/env python3
"""
Database migration script to add the Benchmarking table
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Benchmarking

def create_benchmarking_table():
    """Create the benchmarking table in the database"""
    
    app = create_app()
    
    with app.app_context():
        print("🏗️  Creating Benchmarking table...")
        
        try:
            # Create all tables (this will only create missing ones)
            db.create_all()
            
            print("✅ Benchmarking table created successfully!")
            print("📊 Ready to add benchmarking data!")
            
            # Verify the table was created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'benchmarking' in tables:
                print("🎉 Confirmed: 'benchmarking' table exists in database")
                
                # Show table structure
                columns = inspector.get_columns('benchmarking')
                print(f"\n📋 Table structure ({len(columns)} columns):")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("❌ Error: 'benchmarking' table not found!")
                return False
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False
            
    return True

if __name__ == '__main__':
    print("🚀 PTSA Tracker - Database Migration")
    print("=" * 40)
    
    success = create_benchmarking_table()
    
    if success:
        print("\n✨ Migration completed successfully!")
        print("🔄 You can now run the seed script:")
        print("   python seed_benchmarking_data.py")
    else:
        print("\n❌ Migration failed. Check the errors above.")
        sys.exit(1)