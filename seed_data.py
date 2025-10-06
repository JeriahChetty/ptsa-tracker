"""
Data seeding script for PTSA Tracker
Run this to populate the database with sample data
"""
import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db
from app.models import (
    User, Company, Measure, MeasureStep, MeasureAssignment, 
    AssignmentStep, CompanyBenchmark
)


def seed_database():
    """Seed the database with initial data"""
    # Create app with development config for local seeding
    app = create_app('development')
    
    with app.app_context():
        print("🌱 Starting database seeding...")
        
        # Get the database URI and ensure the directory exists
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"📍 Database URI: {db_uri}")
        
        if db_uri.startswith('sqlite:///'):
            # Extract the database file path
            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                # Relative path - make it relative to project root
                db_path = os.path.join(project_root, db_path)
            
            # Ensure the directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                print(f"📁 Created database directory: {db_dir}")
            
            print(f"📄 Database file will be created at: {db_path}")
        
        # Create tables if they don't exist
        print("🏗️  Creating database tables...")
        try:
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            print("💡 Try running the app first to initialize the database")
            return
        
        # Check if data already exists
        existing_users = User.query.count()
        if existing_users > 0:
            print(f"ℹ️  Database already contains {existing_users} users. Skipping seeding.")
            print("💡 Delete the database file if you want to reseed")
            return
        
        # 1. Create Admin User
        print("👤 Creating admin user...")
        admin = User(
            email='admin@ptsa.co.za',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.flush()
        
        # 2. Create Sample Companies with benchmarking data
        print("🏢 Creating sample companies...")
        companies_data = [
            {
                'name': 'Gehring Technologies SA',
                'region': 'Gauteng',
                'industry_category': 'Precision Tooling & Automation',
                'phone': '+27 11 452 8000',
                'email': 'admin@gehring.co.za',
                'password': 'company123',
                'tech_resources': 'Advanced CNC machining centers, precision grinding equipment, CAD/CAM software, automated production lines',
                'human_resources': 'Highly skilled engineers, certified toolmakers, quality control specialists',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 85,000,000',
                        'tools_produced': 45,
                        'on_time_delivery': '88%',
                        'export_percentage': '35%',
                        'employees': 120,
                        'apprentices': 12,
                        'artisans': 35,
                        'master_artisans': 8,
                        'engineers': 15,
                        'notes': 'Baseline data - strong export performance'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 92,500,000',
                        'tools_produced': 52,
                        'on_time_delivery': '93%',
                        'export_percentage': '42%',
                        'employees': 128,
                        'apprentices': 15,
                        'artisans': 38,
                        'master_artisans': 9,
                        'engineers': 17,
                        'notes': 'Significant improvement in delivery performance and export growth'
                    }
                ]
            },
            {
                'name': 'ACME Precision Manufacturing',
                'region': 'Western Cape',
                'industry_category': 'Automotive Tooling',
                'phone': '+27 21 789 4500',
                'email': 'operations@acmeprecision.co.za',
                'password': 'company123',
                'tech_resources': 'Multi-axis CNC machines, EDM equipment, coordinate measuring machines, ERP system',
                'human_resources': 'Experienced toolmakers, design engineers, project managers',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 67,500,000',
                        'tools_produced': 38,
                        'on_time_delivery': '91%',
                        'export_percentage': '28%',
                        'employees': 95,
                        'apprentices': 8,
                        'artisans': 28,
                        'master_artisans': 6,
                        'engineers': 12,
                        'notes': 'Strong automotive sector focus'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 73,200,000',
                        'tools_produced': 42,
                        'on_time_delivery': '94%',
                        'export_percentage': '31%',
                        'employees': 102,
                        'apprentices': 10,
                        'artisans': 31,
                        'master_artisans': 7,
                        'engineers': 14,
                        'notes': 'Expanded capacity and improved efficiency'
                    }
                ]
            },
            {
                'name': 'Bosch Tooling Solutions',
                'region': 'Gauteng',
                'industry_category': 'Industrial Tooling',
                'phone': '+27 11 651 9800',
                'email': 'info@bosch-tooling.co.za',
                'password': 'company123',
                'tech_resources': 'State-of-the-art machining centers, Industry 4.0 monitoring systems, advanced simulation software',
                'human_resources': 'International expertise, local skilled workforce, continuous training programs',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 145,000,000',
                        'tools_produced': 78,
                        'on_time_delivery': '96%',
                        'export_percentage': '55%',
                        'employees': 185,
                        'apprentices': 18,
                        'artisans': 52,
                        'master_artisans': 12,
                        'engineers': 25,
                        'notes': 'Industry leader with strong international presence'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 156,800,000',
                        'tools_produced': 85,
                        'on_time_delivery': '97%',
                        'export_percentage': '58%',
                        'employees': 195,
                        'apprentices': 22,
                        'artisans': 56,
                        'master_artisans': 14,
                        'engineers': 28,
                        'notes': 'Continued growth and operational excellence'
                    }
                ]
            },
            {
                'name': 'Durban Tool & Die Works',
                'region': 'KwaZulu-Natal',
                'industry_category': 'General Tooling',
                'phone': '+27 31 205 7400',
                'email': 'admin@dtdworks.co.za',
                'password': 'company123',
                'tech_resources': 'Conventional and CNC machining, welding facilities, heat treatment capabilities',
                'human_resources': 'Experienced craftsmen, traditional apprenticeship programs',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 32,500,000',
                        'tools_produced': 28,
                        'on_time_delivery': '85%',
                        'export_percentage': '12%',
                        'employees': 68,
                        'apprentices': 6,
                        'artisans': 22,
                        'master_artisans': 4,
                        'engineers': 5,
                        'notes': 'Traditional family business with local market focus'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 35,800,000',
                        'tools_produced': 31,
                        'on_time_delivery': '89%',
                        'export_percentage': '15%',
                        'employees': 72,
                        'apprentices': 8,
                        'artisans': 24,
                        'master_artisans': 5,
                        'engineers': 6,
                        'notes': 'Gradual improvement and market expansion'
                    }
                ]
            },
            {
                'name': 'Cape Tool & Engineering',
                'region': 'Western Cape',
                'industry_category': 'Marine & Aerospace Tooling',
                'phone': '+27 21 934 5600',
                'email': 'info@capetool.co.za',
                'password': 'company123',
                'tech_resources': 'Specialized marine equipment, precision measuring tools, environmental testing facilities',
                'human_resources': 'Marine engineering specialists, certified welders, quality inspectors',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 48,200,000',
                        'tools_produced': 22,
                        'on_time_delivery': '92%',
                        'export_percentage': '45%',
                        'employees': 78,
                        'apprentices': 4,
                        'artisans': 25,
                        'master_artisans': 8,
                        'engineers': 18,
                        'notes': 'Specialized niche market with high export value'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 52,700,000',
                        'tools_produced': 25,
                        'on_time_delivery': '94%',
                        'export_percentage': '48%',
                        'employees': 82,
                        'apprentices': 6,
                        'artisans': 27,
                        'master_artisans': 9,
                        'engineers': 19,
                        'notes': 'Strong performance in specialized markets'
                    }
                ]
            },
            {
                'name': 'Sandvik Tooling SA',
                'region': 'Gauteng',
                'industry_category': 'Mining & Industrial Tools',
                'phone': '+27 11 570 9000',
                'email': 'sa.admin@sandvik.com',
                'password': 'company123',
                'tech_resources': 'Advanced metallurgy labs, cutting-edge manufacturing technology, global R&D network',
                'human_resources': 'International engineering teams, local technical specialists, comprehensive training center',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 220,000,000',
                        'tools_produced': 125,
                        'on_time_delivery': '98%',
                        'export_percentage': '75%',
                        'employees': 285,
                        'apprentices': 25,
                        'artisans': 78,
                        'master_artisans': 18,
                        'engineers': 45,
                        'notes': 'Global leader in mining and industrial tooling'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 238,500,000',
                        'tools_produced': 135,
                        'on_time_delivery': '98%',
                        'export_percentage': '78%',
                        'employees': 295,
                        'apprentices': 28,
                        'artisans': 82,
                        'master_artisans': 20,
                        'engineers': 48,
                        'notes': 'Sustained excellence and global market expansion'
                    }
                ]
            },
            {
                'name': 'Johannesburg Precision Tools',
                'region': 'Gauteng',
                'industry_category': 'Precision Components',
                'phone': '+27 11 432 8900',
                'email': 'admin@jpttools.co.za',
                'password': 'company123',
                'tech_resources': 'High-precision CNC equipment, optical measuring systems, clean room facilities',
                'human_resources': 'Precision engineering specialists, quality control experts',
                'membership': 'Member',
                'benchmarks': [
                    {
                        'year': 2023,
                        'turnover': 'R 28,800,000',
                        'tools_produced': 35,
                        'on_time_delivery': '87%',
                        'export_percentage': '22%',
                        'employees': 52,
                        'apprentices': 4,
                        'artisans': 18,
                        'master_artisans': 3,
                        'engineers': 8,
                        'notes': 'Smaller operation focused on high-precision work'
                    },
                    {
                        'year': 2024,
                        'turnover': 'R 31,500,000',
                        'tools_produced': 38,
                        'on_time_delivery': '91%',
                        'export_percentage': '25%',
                        'employees': 55,
                        'apprentices': 5,
                        'artisans': 20,
                        'master_artisans': 4,
                        'engineers': 9,
                        'notes': 'Steady growth in precision markets'
                    }
                ]
            }
        ]

        companies = []
        for comp_data in companies_data:
            company = Company(
                name=comp_data['name'],
                region=comp_data['region'],
                industry_category=comp_data['industry_category'],
                phone=comp_data['phone'],
                tech_resources=comp_data['tech_resources'],
                human_resources=comp_data['human_resources'],
                membership=comp_data['membership']
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
            
            # Store company with its data for later use
            companies.append((company, comp_data))

        # 3. Create Sample Measures
        print("📋 Creating sample measures...")
        measures_data = [
            {
                'name': 'Implement 5S Workplace Organization',
                'description': 'Systematic approach to workplace organization and standardization',
                'target': 'Achieve 95% compliance with 5S standards',
                'departments': 'Production, Quality Control',
                'responsible': 'Production Manager',
                'participants': 'All shop floor employees',
                'steps': [
                    'Sort - Remove unnecessary items from workplace',
                    'Set in Order - Organize remaining items systematically',
                    'Shine - Clean and maintain the workplace',
                    'Standardize - Create standards for maintaining organization',
                    'Sustain - Maintain and review the system regularly'
                ]
            },
            {
                'name': 'Quality Management System Enhancement',
                'description': 'Improve quality control processes and documentation',
                'target': 'Reduce defect rate by 30%',
                'departments': 'Quality Control, Production',
                'responsible': 'Quality Manager',
                'participants': 'QC team, Production supervisors',
                'steps': [
                    'Conduct current state assessment',
                    'Identify improvement opportunities',
                    'Develop new quality procedures',
                    'Train staff on new procedures',
                    'Implement monitoring systems',
                    'Review and optimize processes'
                ]
            },
            {
                'name': 'Energy Efficiency Improvement Program',
                'description': 'Reduce energy consumption and improve sustainability',
                'target': 'Reduce energy costs by 20%',
                'departments': 'Facilities, Production',
                'responsible': 'Facilities Manager',
                'participants': 'Maintenance team, Operators',
                'steps': [
                    'Conduct energy audit',
                    'Identify energy waste areas',
                    'Implement energy-saving measures',
                    'Monitor energy consumption',
                    'Train staff on energy conservation'
                ]
            },
            {
                'name': 'Skills Development Program',
                'description': 'Enhance workforce capabilities through structured training',
                'target': 'Train 80% of workforce in new skills',
                'departments': 'HR, Production',
                'responsible': 'HR Manager',
                'participants': 'All employees',
                'steps': [
                    'Assess current skill levels',
                    'Identify skill gaps',
                    'Develop training curriculum',
                    'Conduct training sessions',
                    'Evaluate training effectiveness',
                    'Provide ongoing support'
                ]
            },
            {
                'name': 'Digital Transformation Initiative',
                'description': 'Modernize operations through digital technologies',
                'target': 'Digitize 70% of manual processes',
                'departments': 'IT, Production, Administration',
                'responsible': 'IT Manager',
                'participants': 'Department heads, Key users',
                'steps': [
                    'Assess current digital maturity',
                    'Define digital strategy',
                    'Select appropriate technologies',
                    'Implement pilot projects',
                    'Scale successful solutions',
                    'Provide ongoing support and training'
                ]
            }
        ]
        
        measures = []
        for idx, measure_data in enumerate(measures_data):
            measure = Measure(
                name=measure_data['name'],
                measure_detail=measure_data['description'],
                target=measure_data['target'],
                departments=measure_data['departments'],
                responsible=measure_data['responsible'],
                participants=measure_data['participants'],
                start_date=date.today(),
                end_date=date.today() + timedelta(days=180),
                order=idx + 1  # Set order for proper sorting
            )
            db.session.add(measure)
            db.session.flush()
            
            # Add steps for this measure
            for step_idx, step_title in enumerate(measure_data['steps']):
                step = MeasureStep(
                    measure_id=measure.id,
                    title=step_title,
                    step=step_idx + 1
                )
                db.session.add(step)
            
            measures.append(measure)
        
        # 4. Create Measure Assignments
        print("📝 Creating measure assignments...")
        for i, (company, comp_data) in enumerate(companies):
            # Assign different measures to each company
            measures_to_assign = measures[i:i+3] if i < len(measures) else measures[:2]
            
            for j, measure in enumerate(measures_to_assign):
                due_date = datetime.now() + timedelta(days=30 + (j * 15))
                
                assignment = MeasureAssignment(
                    company_id=company.id,
                    measure_id=measure.id,
                    status='In Progress' if j == 0 else 'Not Started',
                    urgency=2,
                    due_at=due_date,
                    target=measure.target,
                    departments=measure.departments,
                    responsible=measure.responsible,
                    participants=measure.participants
                )
                db.session.add(assignment)
                db.session.flush()
                
                # Create assignment steps from measure steps
                measure_steps = MeasureStep.query.filter_by(measure_id=measure.id).order_by(MeasureStep.step).all()
                for step_idx, measure_step in enumerate(measure_steps):
                    assignment_step = AssignmentStep(
                        assignment_id=assignment.id,
                        title=measure_step.title,
                        step=step_idx + 1,
                        order_index=step_idx,
                        is_completed=(j == 0 and step_idx < 2)  # Mark first few steps as completed for first assignment
                    )
                    db.session.add(assignment_step)
        
        # 5. Create Sample Benchmarking Data
        print("📊 Creating realistic benchmarking data...")
        for company, comp_data in companies:
            for benchmark_data in comp_data['benchmarks']:
                benchmark = CompanyBenchmark(
                    company_id=company.id,
                    data_year=benchmark_data['year'],
                    entered_by_id=admin.id,
                    entered_by_role='admin',
                    turnover=benchmark_data['turnover'],
                    tools_produced=benchmark_data['tools_produced'],
                    on_time_delivery=benchmark_data['on_time_delivery'],
                    export_percentage=benchmark_data['export_percentage'],
                    employees=benchmark_data['employees'],
                    apprentices=benchmark_data['apprentices'],
                    artisans=benchmark_data['artisans'],
                    master_artisans=benchmark_data['master_artisans'],
                    engineers=benchmark_data['engineers'],
                    notes=benchmark_data['notes']
                )
                db.session.add(benchmark)

        # Commit all changes
        print("💾 Saving all data to database...")
        try:
            db.session.commit()
            print("✅ Database seeding completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving to database: {e}")
            return
        
        print("\n📋 Summary:")
        print(f"   • Created 1 admin user")
        print(f"   • Created {len(companies)} realistic companies with users")
        print(f"   • Created {len(measures)} measures with steps")
        print(f"   • Created measure assignments")
        print(f"   • Created realistic benchmarking data with 2 years per company")
        print("\n🔐 Login Credentials:")
        print("   Admin: admin@ptsa.co.za / admin123")
        print("   Companies:")
        for company, comp_data in companies:
            print(f"   • {comp_data['email']} / {comp_data['password']} ({company.name})")
        print(f"\n📄 Database file: {db_path if 'db_path' in locals() else 'In memory or not SQLite'}")


if __name__ == '__main__':
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Seeding failed with error: {e}")
        print("💡 Make sure you're in the project directory and have activated your virtual environment")
        sys.exit(1)
