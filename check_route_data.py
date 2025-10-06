#!/usr/bin/env python3
"""
Check what data should be passed to company profile template
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_route_data():
    """Check what data the company profile route should pass"""
    
    print("🔍 Checking Company Profile Route Data")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.models import Company, CompanyBenchmark
        
        app = create_app()
        
        with app.app_context():
            # Get a sample company
            company = Company.query.first()
            if not company:
                print("❌ No companies found!")
                return False
            
            print(f"🏢 Testing with company: {company.name} (ID: {company.id})")
            
            # Check what benchmarks exist for this company
            benchmarks = CompanyBenchmark.query.filter_by(company_id=company.id).order_by(CompanyBenchmark.data_year).all()
            
            print(f"📊 Found {len(benchmarks)} benchmarks for this company:")
            
            if benchmarks:
                for benchmark in benchmarks:
                    print(f"  📅 {benchmark.data_year}: Turnover={benchmark.turnover}, Tools={benchmark.tools_produced}")
                
                # Show what the template should receive
                print(f"\n✅ Template should receive:")
                print(f"  - company: {company}")
                print(f"  - benchmarks: {benchmarks} (list of {len(benchmarks)} CompanyBenchmark objects)")
                
                # Test template context
                template_context = {
                    'company': company,
                    'benchmarks': benchmarks,
                    'assignments': []  # Would come from measure assignments
                }
                
                print(f"\n🧪 Template context test:")
                print(f"  {{% if benchmarks %}} -> {bool(template_context['benchmarks'])}")
                print(f"  benchmarks|length -> {len(template_context['benchmarks'])}")
                
                return True
            else:
                print("❌ No benchmarks found for this company!")
                
                # Check all benchmarks in database
                all_benchmarks = CompanyBenchmark.query.all()
                print(f"📈 Total benchmarks in database: {len(all_benchmarks)}")
                
                if all_benchmarks:
                    print("📋 All benchmark records:")
                    for b in all_benchmarks:
                        print(f"  Company {b.company_id}, Year {b.data_year}")
                
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_route_data()