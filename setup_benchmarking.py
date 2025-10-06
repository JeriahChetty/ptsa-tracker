#!/usr/bin/env python3
"""
All-in-one script to set up benchmarking functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def setup_benchmarking():
    """Set up complete benchmarking functionality"""
    
    print("🚀 PTSA Tracker - Benchmarking Setup")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.models import Company, Benchmarking
        import random
        
        app = create_app()
        
        with app.app_context():
            # Step 1: Create tables
            print("📋 Step 1: Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Step 2: Check for existing data
            existing_benchmarks = Benchmarking.query.count()
            companies = Company.query.all()
            
            print(f"📊 Found {len(companies)} companies")
            print(f"📈 Found {existing_benchmarks} existing benchmark records")
            
            if existing_benchmarks > 0:
                print("⚠️  Benchmarking data already exists. Skipping seed data creation.")
            else:
                print("🌱 Creating seed data...")
                
                # Create sample data for the first few companies
                sample_companies = companies[:min(3, len(companies))]
                years = [2022, 2023, 2024]
                
                for company in sample_companies:
                    print(f"  📈 Adding data for {company.name}...")
                    
                    base_turnover = random.randint(3000000, 15000000)
                    base_employees = random.randint(25, 80)
                    
                    for year in years:
                        # Create realistic variations
                        year_factor = 1 + random.uniform(-0.1, 0.2)
                        
                        benchmark = Benchmarking(
                            company_id=company.id,
                            data_year=year,
                            turnover=int(base_turnover * year_factor),
                            tools_produced=random.randint(800, 5000),
                            on_time_delivery=random.randint(85, 98),
                            export_percentage=random.randint(0, 20),
                            employees=int(base_employees * random.uniform(0.9, 1.1)),
                            apprentices=random.randint(0, 8),
                            artisans=random.randint(10, 30),
                            master_artisans=random.randint(2, 8),
                            engineers=random.randint(3, 12),
                            notes=f"Sample data for {year}"
                        )
                        
                        db.session.add(benchmark)
                
                # Commit changes
                db.session.commit()
                print("✅ Sample data created successfully!")
            
            print(f"\n🎉 Setup completed successfully!")
            print(f"📊 Your company profiles now have benchmarking functionality!")
            print(f"💡 The 'Add Data' and 'View Charts' buttons now work!")
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False
        
    return True

if __name__ == '__main__':
    setup_benchmarking()