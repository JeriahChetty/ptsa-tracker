#!/usr/bin/env python3
"""
Check existing table structures and fix models
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_existing_tables():
    """Check what's already in the database"""
    
    print("🔍 PTSA Tracker - Existing Table Analysis")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from sqlalchemy import inspect
        
        app = create_app()
        
        with app.app_context():
            inspector = inspect(db.engine)
            
            # Check companies table
            if 'companies' in inspector.get_table_names():
                print("🏢 COMPANIES table structure:")
                columns = inspector.get_columns('companies')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            
            # Check company_benchmarks table  
            if 'company_benchmarks' in inspector.get_table_names():
                print("\n📊 COMPANY_BENCHMARKS table structure:")
                columns = inspector.get_columns('company_benchmarks')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                
                # Check if there's existing data
                result = db.session.execute(db.text("SELECT COUNT(*) FROM company_benchmarks")).scalar()
                print(f"  📈 Existing records: {result}")
            else:
                print("\n❌ No company_benchmarks table found")
            
            # Now test our models
            print(f"\n🧪 Testing model imports...")
            try:
                from app.models import Company
                print(f"  ✅ Company model: table='{Company.__tablename__}'")
                
                # Count companies
                company_count = Company.query.count()
                print(f"     Companies in database: {company_count}")
                
            except Exception as e:
                print(f"  ❌ Company model error: {e}")
            
            try:
                from app.models import Benchmarking
                print(f"  ✅ Benchmarking model: table='{Benchmarking.__tablename__}'")
                
                # Try to query (will fail if table doesn't exist)
                benchmark_count = Benchmarking.query.count()
                print(f"     Benchmarks in database: {benchmark_count}")
                
            except Exception as e:
                print(f"  ❌ Benchmarking model error: {e}")
                
            return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    check_existing_tables()