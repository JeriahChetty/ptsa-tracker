#!/usr/bin/env python3
"""
Database inspection and table creation script
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def inspect_and_fix_database():
    """Inspect existing database structure and fix issues"""
    
    print("🔍 PTSA Tracker - Database Inspector")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from sqlalchemy import inspect
        
        app = create_app()
        
        with app.app_context():
            # Check existing tables
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"📊 Found {len(existing_tables)} existing tables:")
            for table in sorted(existing_tables):
                print(f"  ✅ {table}")
            
            # Try to create all tables
            print(f"\n🏗️  Creating all missing tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = inspect(db.engine)
            final_tables = inspector.get_table_names()
            
            print(f"\n📊 Final table list:")
            for table in sorted(final_tables):
                print(f"  ✅ {table}")
            
            # Check for required tables
            required_tables = ['company', 'benchmarking']
            missing_tables = [t for t in required_tables if t not in final_tables]
            
            if missing_tables:
                print(f"\n❌ Still missing tables: {missing_tables}")
                
                # Try alternative table names
                alternative_names = {
                    'company': ['companies'],
                    'benchmarking': ['benchmark']
                }
                
                for missing in missing_tables:
                    alternatives = alternative_names.get(missing, [])
                    found_alternative = None
                    
                    for alt in alternatives:
                        if alt in final_tables:
                            found_alternative = alt
                            break
                    
                    if found_alternative:
                        print(f"  ℹ️  Found alternative table '{found_alternative}' for '{missing}'")
                    else:
                        print(f"  ❌ No table found for '{missing}'")
                
                return False
            else:
                print(f"\n✅ All required tables exist!")
                return True
                
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = inspect_and_fix_database()
    
    if success:
        print(f"\n🎉 Database setup completed successfully!")
        print(f"✨ You can now run: python setup_benchmarking.py")
    else:
        print(f"\n❌ Database setup failed. Check the errors above.")
        sys.exit(1)