#!/usr/bin/env python3
"""
Quick fix script for the missing database columns error.
This script will add the missing columns to your existing database.
"""

import sqlite3
import os
from datetime import datetime

def quick_fix_database():
    """Quick fix for missing database columns."""
    print("🔧 Quick Database Fix for PTSA Tracker")
    print("=" * 40)
    
    # Database path
    db_path = os.path.join('instance', 'ptsa_tracker.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found at:", db_path)
        print("💡 It looks like the database hasn't been initialized yet.")
        print("\nTo fix this, run:")
        print("  python init_database.py")
        print("\nThis will create a new database with all required tables and sample data.")
        return False
    
    print(f"📊 Found database at: {db_path}")
    
    try:
        # Create backup
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking existing columns...")
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(companies)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"  Current columns: {len(columns)} found")
        
        # Add missing columns
        missing_added = 0
        
        if 'benchmarking_reminder_months' not in columns:
            cursor.execute("ALTER TABLE companies ADD COLUMN benchmarking_reminder_months INTEGER DEFAULT 12")
            print("  ✅ Added benchmarking_reminder_months")
            missing_added += 1
        
        if 'last_benchmarking_reminder' not in columns:
            cursor.execute("ALTER TABLE companies ADD COLUMN last_benchmarking_reminder DATETIME")
            print("  ✅ Added last_benchmarking_reminder")
            missing_added += 1
        
        if 'next_benchmarking_due' not in columns:
            cursor.execute("ALTER TABLE companies ADD COLUMN next_benchmarking_due DATETIME")
            print("  ✅ Added next_benchmarking_due")
            missing_added += 1
        
        # Check if CompanyBenchmark table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_benchmark'")
        if not cursor.fetchone():
            print("📋 Creating CompanyBenchmark table...")
            
            create_table_sql = """
            CREATE TABLE company_benchmark (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                data_year INTEGER NOT NULL,
                entered_by_id INTEGER,
                entered_by_role VARCHAR(50) DEFAULT 'admin',
                turnover DECIMAL(15,2),
                tools_produced INTEGER,
                on_time_delivery DECIMAL(5,2),
                export_percentage DECIMAL(5,2),
                employees INTEGER,
                apprentices INTEGER,
                artisans INTEGER,
                master_artisans INTEGER,
                engineers INTEGER,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                FOREIGN KEY (entered_by_id) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(company_id, data_year)
            )
            """
            cursor.execute(create_table_sql)
            print("  ✅ Created company_benchmark table")
            missing_added += 1
            
            # Create index
            cursor.execute("CREATE INDEX idx_company_benchmark_company_year ON company_benchmark(company_id, data_year)")
            print("  ✅ Added performance index")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if missing_added > 0:
            print(f"\n🎉 Successfully added {missing_added} missing database components!")
        else:
            print("\n✅ Database schema was already up to date!")
        
        print("\n" + "=" * 40)
        print("✅ QUICK FIX COMPLETED!")
        print("You can now start your application with: flask run")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during fix: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = quick_fix_database()
    exit(0 if success else 1)