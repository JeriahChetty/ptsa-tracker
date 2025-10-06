#!/usr/bin/env python3
"""
Export existing database data to include in deployment
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

def export_database_data():
    """Export all data from existing database to JSON"""
    
    # Common database locations
    db_paths = [
        'instance/ptsa.db',
        'instance/ptsa_tracker.db',
        'instance/app.db', 
        'ptsa_tracker.db',
        'app.db',
        'database.db'
    ]
    
    db_path = None
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ No database file found. Looking for database files...")
        for db_file in Path('.').glob('**/*.db'):
            print(f"Found: {db_file}")
        return None
    
    print(f"📁 Exporting data from: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    
    exported_data = {
        'export_timestamp': datetime.now().isoformat(),
        'source_database': str(db_path),
        'tables': {}
    }
    
    try:
        # First, discover all tables in the database
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"🔍 Found tables: {', '.join(tables)}")
        
        # Export all data from each table
        for table_name in tables:
            if table_name == 'sqlite_sequence':  # Skip system table
                continue
                
            try:
                cursor = conn.execute(f'SELECT * FROM {table_name}')
                rows = cursor.fetchall()
                exported_data['tables'][table_name] = [dict(row) for row in rows]
                print(f"✅ Exported {len(exported_data['tables'][table_name])} records from {table_name}")
            except sqlite3.OperationalError as e:
                print(f"⚠️ Error reading table {table_name}: {e}")
        
        # Save to JSON file
        with open('original_data_export.json', 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, indent=2, default=str)
        
        print(f"\n🎉 Data exported successfully to: original_data_export.json")
        
        # Show summary
        print("\n📊 Export Summary:")
        print("=" * 40)
        for table_name, records in exported_data['tables'].items():
            print(f"{table_name}: {len(records)} records")
        
        return exported_data
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        conn.close()

def show_companies_data():
    """Show what companies are in the data"""
    try:
        with open('original_data_export.json', 'r') as f:
            data = json.load(f)
        
        # Check different possible table names for companies
        companies = []
        for table_name, records in data.get('tables', {}).items():
            if 'company' in table_name.lower() or 'organisation' in table_name.lower():
                companies = records
                print(f"\n🏢 Companies found in table '{table_name}':")
                break
        
        if not companies:
            print("\n🔍 Looking for company-like data in all tables...")
            for table_name, records in data.get('tables', {}).items():
                if records:
                    # Check if any record has company-like fields
                    first_record = records[0]
                    if any(field in str(first_record.keys()).lower() for field in ['name', 'company', 'organisation']):
                        print(f"\n📋 Data from table '{table_name}':")
                        for record in records[:5]:  # Show first 5 records
                            name_field = None
                            for key in record.keys():
                                if 'name' in key.lower():
                                    name_field = key
                                    break
                            if name_field:
                                print(f"- {record.get(name_field, 'Unknown')}")
                        if len(records) > 5:
                            print(f"... and {len(records) - 5} more records")
        else:
            print("=" * 50)
            for company in companies:
                name_field = company.get('name') or company.get('company_name') or company.get('organisation_name')
                industry_field = company.get('industry_category') or company.get('industry') or company.get('sector')
                print(f"- {name_field or 'Unknown'} ({industry_field or 'Unknown industry'})")
        
        # Show all tables found
        print(f"\n� All tables in your database:")
        print("=" * 50)
        for table_name, records in data.get('tables', {}).items():
            print(f"- {table_name}: {len(records)} records")
            
    except FileNotFoundError:
        print("❌ No export file found. Run export first.")

if __name__ == '__main__':
    print("🔍 Looking for your original database...")
    
    # Try to export
    result = export_database_data()
    
    if result:
        show_companies_data()
        print(f"\n📝 Next step: Include 'original_data_export.json' in your Docker deployment")
    else:
        print("\n💡 If you have data in a different location, please specify the path to your database file.")