#!/usr/bin/env python3
"""
Quick script to test existing benchmarking functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_existing_benchmarking():
    """Test the existing CompanyBenchmark model"""
    
    print("🧪 Testing Existing Benchmarking")
    print("=" * 40)
    
    try:
        from app import create_app, db
        from app.models import Company, CompanyBenchmark
        
        app = create_app()
        
        with app.app_context():
            # Show existing data
            companies = Company.query.all()
            print(f"📊 Found {len(companies)} companies")
            
            benchmarks = CompanyBenchmark.query.all()
            print(f"📈 Found {len(benchmarks)} benchmark records")
            
            # Show sample data by company
            for company in companies[:3]:  # Show first 3 companies
                company_benchmarks = CompanyBenchmark.query.filter_by(company_id=company.id).order_by(CompanyBenchmark.data_year).all()
                
                if company_benchmarks:
                    print(f"\n🏢 {company.name}:")
                    for bench in company_benchmarks:
                        print(f"  📅 {bench.data_year}: Turnover={bench.turnover}, Tools={bench.tools_produced}, Employees={bench.employees}")
                else:
                    print(f"\n🏢 {company.name}: No benchmarking data")
            
            # Test creating a sample record
            if len(companies) > 0:
                test_company = companies[0]
                
                # Check if 2024 data exists
                existing_2024 = CompanyBenchmark.query.filter_by(
                    company_id=test_company.id,
                    data_year=2024
                ).first()
                
                if not existing_2024:
                    print(f"\n➕ Adding sample 2024 data for {test_company.name}...")
                    
                    new_benchmark = CompanyBenchmark(
                        company_id=test_company.id,
                        data_year=2024,
                        entered_by_id=1,  # Assuming user ID 1 exists
                        entered_by_role='admin',
                        turnover="R 8,500,000",
                        tools_produced=3200,
                        on_time_delivery="94.2",
                        export_percentage="12.5",
                        employees=52,
                        apprentices=4,
                        artisans=22,
                        master_artisans=6,
                        engineers=8,
                        notes="Sample data for testing"
                    )
                    
                    db.session.add(new_benchmark)
                    db.session.commit()
                    print("✅ Added sample 2024 data!")
                else:
                    print(f"ℹ️  2024 data already exists for {test_company.name}")
            
            return True
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_existing_benchmarking()