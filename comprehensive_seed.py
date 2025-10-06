#!/usr/bin/env python3
"""Comprehensive seeding script for PTSA Tracker with realistic South African tooling company data"""

import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from app import create_app
from app.extensions import db
from app.models import (
    User, Company, Measure, MeasureStep, MeasureAssignment, AssignmentStep,
    NotificationConfig, CompanyBenchmark
)
from werkzeug.security import generate_password_hash

def comprehensive_seed():
    print("🌱 Starting comprehensive database seeding...")
    
    # Create the instance directory if it doesn't exist
    instance_dir = project_root / "instance"
    instance_dir.mkdir(exist_ok=True)
    
    # Set specific database paths
    dev_db_path = instance_dir / "ptsa_dev.db"
    prod_db_path = instance_dir / "ptsa.db"
    
    print(f"📍 Target database paths:")
    print(f"   Dev: {dev_db_path}")
    print(f"   Prod: {prod_db_path}")
    
    # Remove existing database files
    for db_path in [dev_db_path, prod_db_path]:
        if db_path.exists():
            db_path.unlink()
            print(f"🗑️ Removed existing database: {db_path}")
    
    # Force environment variables to ensure proper database location
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DATABASE_URL'] = f'sqlite:///{dev_db_path.absolute()}'
    
    # Create app with specific config
    app = create_app()
    
    # Override database URI to ensure file creation
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{dev_db_path.absolute()}'
    
    print(f"🏗️ Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Force a simple write to ensure database file creation
        try:
            # Create a test table to force file creation
            db.session.execute(db.text('CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)'))
            db.session.execute(db.text('INSERT INTO test_table (id) VALUES (1)'))
            db.session.commit()
            db.session.execute(db.text('DROP TABLE test_table'))
            db.session.commit()
            print("✅ Database file creation verified")
        except Exception as e:
            print(f"⚠️ Database creation test failed: {e}")
        
        # Clear existing data
        print("🗑️ Clearing existing data...")
        try:
            # Delete in correct order to avoid foreign key issues
            db.session.execute(db.text('DELETE FROM assignment_steps'))
            db.session.execute(db.text('DELETE FROM measure_assignments'))
            db.session.execute(db.text('DELETE FROM measure_steps'))
            db.session.execute(db.text('DELETE FROM company_benchmarks'))
            db.session.execute(db.text('DELETE FROM measures'))
            db.session.execute(db.text('DELETE FROM users'))
            db.session.execute(db.text('DELETE FROM companies'))
            db.session.execute(db.text('DELETE FROM notification_config'))
            db.session.commit()
            print("✅ Database cleared successfully")
        except Exception as e:
            print(f"⚠️ Clear warning (continuing): {e}")
            db.session.rollback()

        # 1. Create Admin User
        print("👤 Creating admin user...")
        admin = User(
            email='info@ptsa.co.za',
            password=generate_password_hash('info123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.flush()

        # 2. Create Notification Configuration
        print("⚙️ Creating notification configuration...")
        config = NotificationConfig(
            id=1,
            lead_days=7,
            send_hour_utc=8,
            send_minute_utc=0
        )
        db.session.add(config)

        # 3. Create South African Tooling Companies
        print("🏢 Creating realistic South African tooling companies...")
        
        companies_data = [
            {
                'name': 'Gehring Technologies SA',
                'email': 'admin@gehring.co.za',
                'password': 'gehring123',
                'region': 'Gauteng',
                'industry': 'Precision Tooling & Die Making',
                'tech_resources': 'Advanced CNC machining centers, EDM equipment, CMM inspection systems',
                'human_resources': '55 employees including 15 skilled artisans, 5 engineers, 8 apprentices',
                'membership': 'PTSA Member',
                'phone': '+27 11 234 5678'
            },
            {
                'name': 'ACME Precision Manufacturing',
                'email': 'operations@acmeprecision.co.za',
                'password': 'acme123',
                'region': 'Western Cape',
                'industry': 'Automotive Tooling',
                'tech_resources': '5-axis machining, CAD/CAM software, quality control systems',
                'human_resources': '42 employees with focus on automotive precision components',
                'membership': 'PTSA Member',
                'phone': '+27 21 456 7890'
            },
            {
                'name': 'Bosch Tooling Solutions SA',
                'email': 'info@bosch-tooling.co.za',
                'password': 'bosch123',
                'region': 'KwaZulu-Natal',
                'industry': 'Industrial Tooling & Automation',
                'tech_resources': 'Automated production lines, robotic systems, Industry 4.0 integration',
                'human_resources': '78 employees including master artisans and automation specialists',
                'membership': 'PTSA Member',
                'phone': '+27 31 789 0123'
            },
            {
                'name': 'Durban Tool & Die Works',
                'email': 'admin@dtdworks.co.za',
                'password': 'durban123',
                'region': 'KwaZulu-Natal',
                'industry': 'Tool & Die Manufacturing',
                'tech_resources': 'Traditional and CNC toolmaking equipment, heat treatment facilities',
                'human_resources': '35 skilled craftsmen specializing in tool and die work',
                'membership': 'PTSA Member',
                'phone': '+27 31 234 5678'
            },
            {
                'name': 'Cape Tool & Engineering',
                'email': 'info@capetool.co.za',
                'password': 'cape123',
                'region': 'Western Cape',
                'industry': 'Marine & Aerospace Tooling',
                'tech_resources': 'Specialized marine tooling equipment, aerospace-grade materials handling',
                'human_resources': '28 specialized engineers and technicians',
                'membership': 'PTSA Member',
                'phone': '+27 21 567 8901'
            },
            {
                'name': 'Sandvik Tooling SA',
                'email': 'sa.admin@sandvik.com',
                'password': 'sandvik123',
                'region': 'Gauteng',
                'industry': 'Cutting Tools & Mining Equipment',
                'tech_resources': 'Advanced metallurgy, coating technologies, R&D facilities',
                'human_resources': '95 employees including metallurgists and R&D specialists',
                'membership': 'PTSA Member',
                'phone': '+27 11 890 1234'
            },
            {
                'name': 'Johannesburg Precision Tools',
                'email': 'admin@jpttools.co.za',
                'password': 'jpt123',
                'region': 'Gauteng',
                'industry': 'Precision Measuring & Cutting Tools',
                'tech_resources': 'Precision measurement systems, custom tooling manufacture',
                'human_resources': '31 precision specialists and quality inspectors',
                'membership': 'PTSA Member',
                'phone': '+27 11 345 6789'
            },
            {
                'name': 'Atlas Die Casting Solutions',
                'email': 'info@atlasdie.co.za',
                'password': 'atlas123',
                'region': 'Eastern Cape',
                'industry': 'Die Casting & Metal Forming',
                'tech_resources': 'Die casting machines, metal forming presses, finishing equipment',
                'human_resources': '48 operators and die casting specialists',
                'membership': 'PTSA Member',
                'phone': '+27 41 678 9012'
            }
        ]

        companies = []
        for comp_data in companies_data:
            company = Company(
                name=comp_data['name'],
                region=comp_data['region'],
                industry_category=comp_data['industry'],
                tech_resources=comp_data['tech_resources'],
                human_resources=comp_data['human_resources'],
                membership=comp_data['membership'],
                phone=comp_data['phone'],
                benchmarking_reminder_months=12
            )
            db.session.add(company)
            db.session.flush()

            # Create company user
            user = User(
                email=comp_data['email'],
                password=generate_password_hash(comp_data['password']),
                role='company',
                is_active=True,
                company_id=company.id
            )
            db.session.add(user)
            companies.append((company, comp_data))

        # 4. Create Comprehensive Measures
        print("📋 Creating comprehensive improvement measures...")
        
        measures_data = [
            {
                'name': 'Implement 5S Workplace Organization',
                'detail': 'Systematic approach to workplace organization focusing on Sort, Set in Order, Shine, Standardize, and Sustain principles to improve efficiency and safety.',
                'target': 'Achieve 90% compliance with 5S standards across all work areas',
                'departments': 'Production, Quality Control, Maintenance',
                'responsible': 'Production Manager',
                'participants': 'All shop floor employees, supervisors, quality inspectors',
                'steps': [
                    'Sort (Seiri) - Remove unnecessary items from workspace',
                    'Set in Order (Seiton) - Organize necessary items for easy access',
                    'Shine (Seiso) - Clean and inspect work areas thoroughly',
                    'Standardize (Seiketsu) - Establish standard procedures and schedules',
                    'Sustain (Shitsuke) - Maintain discipline and continuous improvement'
                ]
            },
            {
                'name': 'Setup Time Reduction Program',
                'detail': 'Systematic reduction of machine setup and changeover times using SMED (Single Minute Exchange of Dies) methodology to improve productivity.',
                'target': 'Reduce average setup time by 50% within 6 months',
                'departments': 'Production, Tooling, Maintenance',
                'responsible': 'Manufacturing Engineer',
                'participants': 'Machine operators, toolmakers, maintenance technicians',
                'steps': [
                    'Document current setup procedures and times',
                    'Identify internal vs external setup activities',
                    'Convert internal activities to external where possible',
                    'Streamline remaining internal activities',
                    'Implement quick-change tooling and fixtures',
                    'Train operators on new procedures',
                    'Monitor and continuously improve setup times'
                ]
            },
            {
                'name': 'Total Productive Maintenance (TPM) Implementation',
                'detail': 'Comprehensive maintenance strategy involving all employees to maximize equipment effectiveness and minimize downtime.',
                'target': 'Achieve 95% equipment availability and reduce maintenance costs by 20%',
                'departments': 'Maintenance, Production, Engineering',
                'responsible': 'Maintenance Manager',
                'participants': 'Maintenance team, machine operators, engineers',
                'steps': [
                    'Conduct equipment assessment and criticality analysis',
                    'Implement autonomous maintenance by operators',
                    'Establish planned maintenance schedules',
                    'Train operators in basic maintenance tasks',
                    'Implement condition monitoring systems',
                    'Develop maintenance standards and procedures'
                ]
            },
            {
                'name': 'Quality Management System Enhancement',
                'detail': 'Strengthen quality control processes and implement advanced quality assurance methodologies to reduce defects and improve customer satisfaction.',
                'target': 'Reduce defect rate to less than 1% and achieve ISO certification',
                'departments': 'Quality Control, Production, Engineering',
                'responsible': 'Quality Manager',
                'participants': 'QC inspectors, production supervisors, engineers',
                'steps': [
                    'Review and update quality control procedures',
                    'Implement statistical process control (SPC)',
                    'Train employees in quality awareness',
                    'Establish supplier quality requirements',
                    'Implement corrective and preventive action system',
                    'Prepare for ISO certification audit'
                ]
            },
            {
                'name': 'Energy Efficiency Improvement Program',
                'detail': 'Comprehensive energy audit and efficiency improvement program to reduce energy consumption and environmental impact.',
                'target': 'Reduce energy consumption by 25% within 12 months',
                'departments': 'Facilities, Production, Engineering',
                'responsible': 'Facilities Manager',
                'participants': 'All employees, energy consultants, engineers',
                'steps': [
                    'Conduct comprehensive energy audit',
                    'Identify energy-saving opportunities',
                    'Implement LED lighting upgrades',
                    'Optimize compressed air systems',
                    'Install energy monitoring systems',
                    'Train employees in energy conservation'
                ]
            },
            {
                'name': 'Waste Reduction and Recycling Initiative',
                'detail': 'Systematic approach to minimize waste generation and maximize recycling to improve environmental performance and reduce costs.',
                'target': 'Reduce waste generation by 40% and achieve 80% recycling rate',
                'departments': 'Production, Facilities, Purchasing',
                'responsible': 'Environmental Coordinator',
                'participants': 'All employees, waste management team',
                'steps': [
                    'Conduct waste stream analysis',
                    'Implement material segregation systems',
                    'Establish recycling partnerships',
                    'Train employees in waste reduction practices',
                    'Monitor and report waste metrics',
                    'Implement continuous improvement process'
                ]
            },
            {
                'name': 'Employee Skills Development Program',
                'detail': 'Comprehensive training and development program to enhance employee skills, productivity, and job satisfaction.',
                'target': 'Achieve 90% employee participation in training programs',
                'departments': 'Human Resources, All Departments',
                'responsible': 'HR Manager',
                'participants': 'All employees, external trainers, supervisors',
                'steps': [
                    'Conduct skills gap analysis',
                    'Develop individual development plans',
                    'Implement technical skills training',
                    'Provide leadership development programs',
                    'Establish mentoring systems',
                    'Evaluate training effectiveness'
                ]
            },
            {
                'name': 'Digital Transformation Initiative',
                'detail': 'Modernization of processes through digital technologies including automation, data analytics, and digital documentation systems.',
                'target': 'Digitize 80% of manual processes and implement IoT monitoring',
                'departments': 'IT, Engineering, Production',
                'responsible': 'IT Manager',
                'participants': 'IT team, engineers, production supervisors',
                'steps': [
                    'Assess current digital maturity',
                    'Develop digital transformation roadmap',
                    'Implement digital documentation systems',
                    'Deploy IoT sensors for equipment monitoring',
                    'Integrate data analytics platforms',
                    'Train employees on new digital tools'
                ]
            }
        ]

        measures = []
        for i, measure_data in enumerate(measures_data):
            measure = Measure(
                name=measure_data['name'],
                measure_detail=measure_data['detail'],
                target=measure_data['target'],
                departments=measure_data['departments'],
                responsible=measure_data['responsible'],
                participants=measure_data['participants']
                # Removed default_duration_days and default_urgency as they don't exist in the model
            )
            db.session.add(measure)
            db.session.flush()

            # Add steps
            for step_idx, step_title in enumerate(measure_data['steps']):
                step = MeasureStep(
                    measure_id=measure.id,
                    title=step_title,
                    step=step_idx + 1
                )
                db.session.add(step)

            measures.append(measure)

        # 5. Create Measure Assignments
        print("📝 Creating measure assignments...")
        
        for company, comp_data in companies:
            # Assign 3-5 random measures to each company
            assigned_measures = random.sample(measures, k=random.randint(3, 5))
            
            for measure in assigned_measures:
                # Create assignment with realistic status
                statuses = ['Not Started', 'In Progress', 'Completed']
                weights = [0.2, 0.6, 0.2]  # More likely to be in progress
                status = random.choices(statuses, weights=weights)[0]
                
                assignment = MeasureAssignment(
                    company_id=company.id,
                    measure_id=measure.id,
                    status=status,
                    urgency=random.choice([1, 2, 2, 3]),  # Weighted toward normal priority
                    created_at=datetime.now() - timedelta(days=random.randint(30, 180)),
                    due_at=datetime.now() + timedelta(days=random.randint(30, 120)),
                    target=measure.target,
                    departments=measure.departments,
                    responsible=measure.responsible,
                    participants=measure.participants
                )
                db.session.add(assignment)
                db.session.flush()

                # Create assignment steps based on measure steps
                measure_steps = MeasureStep.query.filter_by(measure_id=measure.id).order_by(MeasureStep.step).all()
                
                for step_template in measure_steps:
                    # Determine completion based on assignment status
                    is_completed = False
                    if status == 'Completed':
                        is_completed = True
                    elif status == 'In Progress':
                        is_completed = random.choice([True, False])  # Some steps completed
                    
                    assignment_step = AssignmentStep(
                        assignment_id=assignment.id,
                        title=step_template.title,
                        step=step_template.step,
                        order_index=step_template.step,
                        is_completed=is_completed,
                        completed_at=datetime.now() - timedelta(days=random.randint(1, 30)) if is_completed else None
                    )
                    db.session.add(assignment_step)

        # 6. Create Benchmarking Data
        print("📊 Creating comprehensive benchmarking data...")
        
        current_year = datetime.now().year
        
        for company, comp_data in companies:
            # Create 2 years of benchmarking data per company
            for year_offset in [1, 0]:  # Previous year and current year
                data_year = current_year - year_offset
                
                # Generate realistic metrics based on company type and size
                base_employees = random.randint(25, 100)
                
                benchmark = CompanyBenchmark(
                    company_id=company.id,
                    data_year=data_year,
                    entered_by_id=admin.id,
                    entered_by_role='admin',
                    
                    # Financial metrics
                    turnover=f"R {random.randint(5, 50)},{random.randint(0, 999):03d},{random.randint(0, 999):03d}.00",
                    
                    # Production metrics
                    tools_produced=random.randint(10, 50),
                    
                    # Performance metrics  
                    on_time_delivery=f"{random.randint(85, 98)}%",
                    export_percentage=f"{random.randint(5, 35)}%",
                    
                    # Human resources metrics
                    employees=base_employees + random.randint(-5, 10),
                    apprentices=random.randint(3, 12),
                    artisans=random.randint(8, 25),
                    master_artisans=random.randint(2, 8),
                    engineers=random.randint(1, 8),
                    
                    notes=f"Benchmarking data for {data_year} - {'Baseline year' if year_offset == 1 else 'Current performance'}"
                )
                db.session.add(benchmark)

        # 7. Commit all data and verify file creation
        print("💾 Saving all data to database...")
        db.session.commit()
        
        # Force database file flush
        try:
            db.session.execute(db.text('PRAGMA wal_checkpoint(TRUNCATE)'))
            db.session.commit()
        except Exception as e:
            print(f"⚠️ WAL checkpoint failed: {e}")
        
        # Verify database file was created
        if dev_db_path.exists():
            print(f"✅ Database file created successfully: {dev_db_path}")
            file_size = dev_db_path.stat().st_size
            print(f"📄 Database file size: {file_size:,} bytes")
            
            # Copy to production location
            import shutil
            shutil.copy2(dev_db_path, prod_db_path)
            print(f"📄 Database copied to production: {prod_db_path}")
        else:
            print(f"❌ Database file was not created at expected location: {dev_db_path}")
            # Try to find where it actually got created
            print("🔍 Searching for database files...")
            for item in Path.cwd().rglob("*.db"):
                if item.stat().st_size > 10000:  # Only show substantial database files
                    print(f"   Found DB file: {item} ({item.stat().st_size:,} bytes)")
                    if "ptsa" in item.name.lower() or item.stat().st_size > 50000:
                        print(f"📁 Copying {item} to {dev_db_path}")
                        import shutil
                        shutil.copy2(item, dev_db_path)
                        shutil.copy2(item, prod_db_path)
                        break
            else:
                return False

        print("✅ Comprehensive database seeding completed successfully!")
        
        # Print summary
        print(f"\n📋 Seeding Summary:")
        print(f"   • Created 1 admin user")
        print(f"   • Created 8 realistic South African tooling companies")
        print(f"   • Created 8 comprehensive improvement measures")
        print(f"   • Created measure assignments with realistic progress")
        print(f"   • Created benchmarking data with 2 years per company")
        print(f"   • Set up notification configuration")
        
        print(f"\n🔐 Login Credentials:")
        print(f"   Admin: info@ptsa.co.za / info123")
        print(f"\n   Companies:")
        company_logins = [
            "admin@gehring.co.za / gehring123 (Gehring Technologies SA)",
            "operations@acmeprecision.co.za / acme123 (ACME Precision Manufacturing)",
            "info@bosch-tooling.co.za / bosch123 (Bosch Tooling Solutions SA)",
            "admin@dtdworks.co.za / durban123 (Durban Tool & Die Works)",
            "info@capetool.co.za / cape123 (Cape Tool & Engineering)",
            "sa.admin@sandvik.com / sandvik123 (Sandvik Tooling SA)",
            "admin@jpttools.co.za / jpt123 (Johannesburg Precision Tools)",
            "info@atlasdie.co.za / atlas123 (Atlas Die Casting Solutions)"
        ]
        for login in company_logins:
            print(f"   • {login}")
        
        print(f"\n📄 Database files created:")
        print(f"   • {dev_db_path}")
        print(f"   • {prod_db_path}")
        print(f"\n🎉 Ready to deploy! Your PTSA Tracker now has comprehensive realistic data.")
        
        return True

if __name__ == "__main__":
    try:
        success = comprehensive_seed()
        if not success:
            print("❌ Comprehensive seeding failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Comprehensive seeding failed with error: {e}")
        print("💡 Make sure you're in the project directory and have activated your virtual environment")
        sys.exit(1)

