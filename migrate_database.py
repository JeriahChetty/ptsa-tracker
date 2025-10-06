#!/usr/bin/env python3
"""
Database migration script to add missing columns for benchmarking features.
Run this script to update your database schema.
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the database migration to add missing columns."""
    try:
        from app import create_app
        from app.extensions import db
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            print("🔄 Starting database migration...")
            
            # Check if we're using SQLite
            if 'sqlite' in str(db.engine.url):
                print("📊 Detected SQLite database")
                
                # Get the database connection
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                
                try:
                    # Check if columns already exist
                    cursor.execute("PRAGMA table_info(companies)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    missing_columns = []
                    
                    # Check each new column
                    new_columns = [
                        'benchmarking_reminder_months',
                        'last_benchmarking_reminder',
                        'next_benchmarking_due'
                    ]
                    
                    for col in new_columns:
                        if col not in columns:
                            missing_columns.append(col)
                    
                    if not missing_columns:
                        print("✅ All columns already exist - no migration needed!")
                        return True
                    
                    print(f"📝 Adding missing columns: {', '.join(missing_columns)}")
                    
                    # Add missing columns
                    if 'benchmarking_reminder_months' in missing_columns:
                        cursor.execute("ALTER TABLE companies ADD COLUMN benchmarking_reminder_months INTEGER DEFAULT 12")
                        print("  ✅ Added benchmarking_reminder_months column")
                    
                    if 'last_benchmarking_reminder' in missing_columns:
                        cursor.execute("ALTER TABLE companies ADD COLUMN last_benchmarking_reminder DATETIME")
                        print("  ✅ Added last_benchmarking_reminder column")
                    
                    if 'next_benchmarking_due' in missing_columns:
                        cursor.execute("ALTER TABLE companies ADD COLUMN next_benchmarking_due DATETIME")
                        print("  ✅ Added next_benchmarking_due column")
                    
                    # Commit the changes
                    connection.commit()
                    print("💾 Changes committed to database")
                    
                    # Check if CompanyBenchmark table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_benchmark'")
                    if not cursor.fetchone():
                        print("📋 Creating CompanyBenchmark table...")
                        
                        # Create the CompanyBenchmark table
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
                        
                        # Create index for better performance
                        cursor.execute("CREATE INDEX idx_company_benchmark_company_year ON company_benchmark(company_id, data_year)")
                        print("  ✅ Added performance index")
                        
                        connection.commit()
                    else:
                        print("✅ CompanyBenchmark table already exists")
                    
                except Exception as e:
                    print(f"❌ Error during migration: {str(e)}")
                    connection.rollback()
                    raise
                finally:
                    cursor.close()
                    connection.close()
                
            else:
                # For other databases, use SQLAlchemy's create_all
                print("📊 Using SQLAlchemy migration for non-SQLite database")
                db.create_all()
                print("✅ Database schema updated")
            
            print("🎉 Migration completed successfully!")
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you're running this script from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def backup_database():
    """Create a backup of the database before migration."""
    import shutil
    
    db_path = 'instance/ptsa_tracker.db'
    if os.path.exists(db_path):
        backup_path = f'instance/ptsa_tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(db_path, backup_path)
        print(f"💾 Database backup created: {backup_path}")
        return backup_path
    else:
        print("ℹ️  No existing database found - no backup needed")
        return None

def main():
    """Main migration function."""
    print("🚀 PTSA Tracker Database Migration")
    print("=" * 40)
    
    # Create backup
    backup_path = backup_database()
    
    # Run migration
    success = run_migration()
    
    if success:
        print("\n" + "=" * 40)
        print("✅ Migration completed successfully!")
        print("You can now start the application with: flask run")
        if backup_path:
            print(f"💡 Database backup available at: {backup_path}")
    else:
        print("\n" + "=" * 40)
        print("❌ Migration failed!")
        if backup_path:
            print(f"💡 Restore from backup if needed: {backup_path}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())