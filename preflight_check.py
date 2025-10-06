#!/usr/bin/env python3
"""
Pre-flight check script for PTSA Tracker application.
Run this script before starting the application to verify everything is set up correctly.
"""

import sys
import os
import traceback
from pathlib import Path

def check_imports():
    """Check if all required imports are available."""
    print("🔍 Checking imports...")
    
    required_packages = [
        'flask',
        'flask_login',
        'flask_mail',
        'sqlalchemy',
        'werkzeug',
    ]
    
    optional_packages = [
        'openpyxl',  # For Excel export
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (REQUIRED)")
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package} (optional)")
        except ImportError:
            print(f"  ⚠️  {package} (optional - Excel export will fallback to CSV)")
            missing_optional.append(package)
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Run: pip install " + " ".join(missing_required))
        return False
    
    print("✅ All required imports available")
    return True

def check_file_structure():
    """Check if all required files and directories exist."""
    print("\n🗂️  Checking file structure...")
    
    required_files = [
        'app/__init__.py',
        'app/models.py',
        'app/routes/admin_routes.py',
        'app/routes/company_routes.py',
        'app/templates/admin/company_benchmarking_history.html',
        'app/templates/admin/company_settings.html',
        'app/static/js/benchmarking-charts.js',
    ]
    
    required_dirs = [
        'app/static/js',
        'app/static/css',
        'app/templates/admin',
        'app/templates/company',
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"  ❌ Missing file: {file_path}")
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    for dir_path in required_dirs:
        if not Path(dir_path).is_dir():
            print(f"  ❌ Missing directory: {dir_path}")
            missing_dirs.append(dir_path)
        else:
            print(f"  ✅ {dir_path}/")
    
    if missing_files or missing_dirs:
        print(f"\n❌ Missing files: {len(missing_files)}, Missing directories: {len(missing_dirs)}")
        return False
    
    print("✅ All required files and directories present")
    return True

def check_models():
    """Check if the models can be imported and have required attributes."""
    print("\n📊 Checking models...")
    
    try:
        # Add the project root to Python path
        sys.path.insert(0, os.getcwd())
        
        from app.models import Company, CompanyBenchmark, User, MeasureAssignment
        
        # Check Company model
        if hasattr(Company, 'benchmarks'):
            print("  ✅ Company.benchmarks relationship")
        else:
            print("  ❌ Company.benchmarks relationship missing")
            return False
        
        # Check CompanyBenchmark model
        required_fields = ['company_id', 'data_year', 'entered_by_role', 'turnover', 'tools_produced']
        for field in required_fields:
            if hasattr(CompanyBenchmark, field):
                print(f"  ✅ CompanyBenchmark.{field}")
            else:
                print(f"  ❌ CompanyBenchmark.{field} missing")
                return False
        
        print("✅ All models check out")
        return True
        
    except Exception as e:
        print(f"❌ Model import error: {str(e)}")
        traceback.print_exc()
        return False

def check_routes():
    """Check if new routes are properly defined."""
    print("\n🛣️  Checking routes...")
    
    try:
        sys.path.insert(0, os.getcwd())
        
        from app.routes.admin_routes import admin_bp
        from app.routes.company_routes import company_bp
        
        # Check admin routes
        admin_rules = [rule.rule for rule in admin_bp.url_map.iter_rules()]
        
        required_admin_routes = [
            '/admin/companies/benchmarking-history',
            '/admin/companies/<int:company_id>/benchmarking',
            '/admin/companies/<int:company_id>/settings',
        ]
        
        for route in required_admin_routes:
            # Check if route pattern exists (basic check)
            if any(route.replace('<int:company_id>', '').replace('<int:', '').replace('>', '') in rule for rule in admin_rules):
                print(f"  ✅ Admin route: {route}")
            else:
                print(f"  ❌ Missing admin route: {route}")
                return False
        
        print("✅ All routes properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Route check error: {str(e)}")
        traceback.print_exc()
        return False

def check_database_schema():
    """Check if the database schema is up to date."""
    print("\n�️  Checking database schema...")
    
    try:
        sys.path.insert(0, os.getcwd())
        
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            # Check if we can query basic tables
            try:
                from app.models import Company, User, CompanyBenchmark
                
                # Test basic queries
                company_count = Company.query.count()
                print(f"  ✅ Companies table accessible ({company_count} records)")
                
                # Check for new columns
                try:
                    # Try to access new columns
                    test_company = Company.query.first()
                    if test_company:
                        _ = test_company.benchmarking_reminder_months
                        _ = test_company.last_benchmarking_reminder
                        _ = test_company.next_benchmarking_due
                    print("  ✅ Company benchmarking columns present")
                except Exception as e:
                    print(f"  ❌ Missing Company columns: {str(e)}")
                    print("  💡 Run: python migrate_database.py")
                    return False
                
                # Check CompanyBenchmark table
                try:
                    benchmark_count = CompanyBenchmark.query.count()
                    print(f"  ✅ CompanyBenchmark table accessible ({benchmark_count} records)")
                except Exception as e:
                    print(f"  ❌ CompanyBenchmark table issue: {str(e)}")
                    print("  💡 Run: python migrate_database.py")
                    return False
                
                print("✅ Database schema is up to date")
                return True
                
            except Exception as e:
                print(f"  ❌ Database query error: {str(e)}")
                return False
                
    except Exception as e:
        print(f"❌ Database check error: {str(e)}")
        return False

def check_javascript():
    """Check if JavaScript files are properly structured."""
    print("\n🔧 Checking JavaScript...")
    
    js_file = Path('app/static/js/benchmarking-charts.js')
    
    if not js_file.exists():
        print("❌ benchmarking-charts.js not found")
        return False
    
    content = js_file.read_text()
    
    required_elements = [
        'yearDistributionChart',
        'entrySourceChart', 
        'Chart(',
        'DOMContentLoaded',
        'dataset.yearLabels',
        'dataset.adminCount'
    ]
    
    for element in required_elements:
        if element in content:
            print(f"  ✅ {element}")
        else:
            print(f"  ❌ Missing: {element}")
            return False
    
    print("✅ JavaScript files properly structured")
    return True

def main():
    """Run all pre-flight checks."""
    print("🚀 PTSA Tracker Pre-Flight Check")
    print("=" * 40)
    
    checks = [
        check_imports,
        check_file_structure,
        check_models,
        check_routes,
        check_database_schema,
        check_javascript,
    ]
    
    all_passed = True
    
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 40)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Ready to run the application.")
        print("\nNext steps:")
        print("1. Start the application: flask run")
        return 0
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Database issues: python migrate_database.py")
        print("2. Missing packages: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())