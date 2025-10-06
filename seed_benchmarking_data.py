#!/usr/bin/env python3
"""
Seed script to populate benchmarking data for PTSA Tracker
This script adds realistic manufacturing industry benchmarking data for all companies
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Company, Benchmarking
import random
from datetime import datetime

def create_realistic_benchmarking_data():
    """Create realistic benchmarking data for manufacturing companies"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting benchmarking data seeding...")
        
        # Get all companies
        companies = Company.query.all()
        if not companies:
            print("❌ No companies found. Please add companies first.")
            return
        
        print(f"📊 Found {len(companies)} companies to populate with data")
        
        # Define realistic data ranges for manufacturing companies
        base_data = {
            'turnover_ranges': {
                'small': (2000000, 8000000),      # R2M - R8M
                'medium': (8000000, 18000000),    # R8M - R18M  
                'large': (18000000, 35000000)     # R18M - R35M
            },
            'tools_ranges': {
                'small': (500, 3000),
                'medium': (3000, 8000),
                'large': (8000, 20000)
            },
            'employee_ranges': {
                'small': (15, 45),
                'medium': (45, 85),
                'large': (85, 150)
            }
        }
        
        # Years to populate (last 5 years)
        years = [2020, 2021, 2022, 2023, 2024]
        
        total_records = 0
        
        for company in companies:
            # Determine company size category
            size_category = random.choice(['small', 'medium', 'large'])
            
            print(f"  📈 Processing {company.name} ({size_category} company)...")
            
            # Base values for consistency across years
            base_turnover = random.randint(*base_data['turnover_ranges'][size_category])
            base_tools = random.randint(*base_data['tools_ranges'][size_category])
            base_employees = random.randint(*base_data['employee_ranges'][size_category])
            
            for year in years:
                # Check if data already exists
                existing = Benchmarking.query.filter_by(
                    company_id=company.id,
                    data_year=year
                ).first()
                
                if existing:
                    print(f"    ⚠️  Data for {year} already exists, skipping...")
                    continue
                
                # Calculate growth/decline factors (realistic business fluctuations)
                year_factor = 1 + random.uniform(-0.15, 0.25)  # -15% to +25% variation
                efficiency_factor = 1 + random.uniform(-0.10, 0.15)  # -10% to +15% efficiency changes
                
                # Calculate realistic metrics
                turnover = int(base_turnover * year_factor)
                tools_produced = int(base_tools * year_factor * efficiency_factor)
                employees = max(10, int(base_employees * random.uniform(0.9, 1.1)))
                
                # Calculate derived metrics
                on_time_delivery = random.randint(82, 98)
                export_percentage = random.randint(0, 25) if random.random() > 0.3 else 0
                
                # Employee breakdown (realistic ratios for manufacturing)
                apprentices = random.randint(0, max(1, employees // 8))
                artisans = random.randint(employees // 4, employees // 2)
                master_artisans = random.randint(1, max(1, artisans // 5))
                engineers = random.randint(2, max(2, employees // 10))
                
                # Ensure totals make sense
                other_employees = max(0, employees - apprentices - artisans - master_artisans - engineers)
                if other_employees < 0:
                    # Adjust if we over-allocated
                    apprentices = max(0, apprentices + other_employees // 4)
                    artisans = max(1, artisans + other_employees // 2)
                
                # Create benchmarking record
                benchmark = Benchmarking(
                    company_id=company.id,
                    data_year=year,
                    turnover=turnover,
                    tools_produced=tools_produced,
                    on_time_delivery=on_time_delivery,
                    export_percentage=export_percentage,
                    employees=employees,
                    apprentices=apprentices,
                    artisans=artisans,
                    master_artisans=master_artisans,
                    engineers=engineers,
                    notes=f"Automated seed data for {year}. {size_category.title()} manufacturing company profile."
                )
                
                db.session.add(benchmark)
                total_records += 1
                
                print(f"    ✅ Added {year}: R{turnover:,.0f} turnover, {tools_produced:,} tools, {employees} employees")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Successfully created {total_records} benchmarking records!")
            print(f"📊 Data spans {len(years)} years ({min(years)}-{max(years)}) for {len(companies)} companies")
            print("\n💡 You can now view the colorful benchmarking tables in company profiles!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving data: {e}")
            return False
            
    return True

if __name__ == '__main__':
    print("🏭 PTSA Tracker - Benchmarking Data Seeder")
    print("=" * 50)
    
    success = create_realistic_benchmarking_data()
    
    if success:
        print("\n✨ Seed data creation completed successfully!")
        print("🚀 Your PTSA Tracker now has realistic benchmarking data!")
    else:
        print("\n❌ Seed data creation failed. Check the errors above.")
        sys.exit(1)