#!/usr/bin/env python3
"""
Check existing models and avoid conflicts
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_existing_models():
    """Check what models already exist"""
    
    print("🔍 PTSA Tracker - Model Analysis")
    print("=" * 50)
    
    try:
        # Import app without models first
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Check what's already in the models file
            import app.models as models
            import inspect
            
            print("📋 Existing model classes:")
            for name, obj in inspect.getmembers(models):
                if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
                    print(f"  ✅ {name}: table='{obj.__tablename__}'")
                    
                    # Check if it's benchmarking related
                    if 'benchmark' in obj.__tablename__.lower():
                        print(f"     🎯 This looks like benchmarking! Let's use this one.")
                        
                        # Show columns
                        if hasattr(obj, '__table__'):
                            columns = [col.name for col in obj.__table__.columns]
                            print(f"     Columns: {', '.join(columns)}")
            
            # Check table contents
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'company_benchmarks' in inspector.get_table_names():
                print(f"\n📊 COMPANY_BENCHMARKS table exists!")
                columns = inspector.get_columns('company_benchmarks')
                print(f"  Columns in database:")
                for col in columns:
                    print(f"    - {col['name']}: {col['type']}")
                
                # Check data count
                result = db.session.execute(db.text("SELECT COUNT(*) FROM company_benchmarks")).scalar()
                print(f"  📈 Records: {result}")
                
                if result > 0:
                    print(f"  🎉 Data already exists! No need to seed.")
                    # Show a sample
                    sample = db.session.execute(db.text("SELECT * FROM company_benchmarks LIMIT 3")).fetchall()
                    if sample:
                        print(f"  📋 Sample data:")
                        for row in sample:
                            print(f"    Company {row[1]}, Year {row[2] if len(row) > 2 else 'N/A'}")
            
            return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_existing_models()