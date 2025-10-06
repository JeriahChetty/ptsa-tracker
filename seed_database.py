#!/usr/bin/env python3
"""
Database seeding script for PTSA Tracker
Creates initial admin and test data, plus imports original data if available
"""

from app import create_app, db
from app.models import User, Company, Measure, MeasureAssignment
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json
from pathlib import Path

def seed_database():
    """Seed the database with initial data"""
    
    app = create_app()
    with app.app_context():
        print("🌱 Starting database seeding...")
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin already exists
        if User.query.filter_by(email='admin@ptsa.com').first():
            print("⚠️ Admin user already exists, skipping...")
            return
        
        # Create admin user
        admin = User(
            email='admin@ptsa.com',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            first_name='System',
            last_name='Administrator',
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        print("✅ Admin user created: admin@ptsa.com / admin123")
        
        # Create test companies
        companies_data = [
            {
                'name': 'Acme Manufacturing',
                'region': 'South Africa',
                'industry_category': 'Manufacturing',
                'email': 'company1@test.com',
                'username': 'acme',
                'password': 'company123'
            },
            {
                'name': 'Tech Solutions Ltd',
                'region': 'South Africa', 
                'industry_category': 'Technology',
                'email': 'company2@test.com',
                'username': 'techsol',
                'password': 'company123'
            },
            {
                'name': 'Green Energy Corp',
                'region': 'South Africa',
                'industry_category': 'Energy',
                'email': 'company3@test.com', 
                'username': 'greenenergy',
                'password': 'company123'
            }
        ]
        
        for company_data in companies_data:
            # Create company
            company = Company(
                name=company_data['name'],
                region=company_data['region'],
                industry_category=company_data['industry_category'],
                created_at=datetime.utcnow()
            )
            db.session.add(company)
            db.session.flush()  # Get company ID
            
            # Create company user
            company_user = User(
                email=company_data['email'],
                username=company_data['username'],
                password_hash=generate_password_hash(company_data['password']),
                role='company',
                company_id=company.id,
                first_name='Test',
                last_name='User',
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.session.add(company_user)
            print(f"✅ Company created: {company_data['name']} ({company_data['email']} / {company_data['password']})")
        
        # Create sample measures (PTSA-specific)
        measures_data = [
            {
                'name': 'Environmental Management System',
                'description': 'Implement ISO 14001 environmental management system',
                'category': 'Environmental',
                'priority': 'High',
                'compliance_standard': 'ISO 14001'
            },
            {
                'name': 'Occupational Health & Safety Program',
                'description': 'Establish comprehensive workplace safety training and procedures',
                'category': 'Safety',
                'priority': 'High',
                'compliance_standard': 'OHSAS 18001'
            },
            {
                'name': 'Water Management Plan',
                'description': 'Implement water conservation and quality management measures',
                'category': 'Environmental',
                'priority': 'High',
                'compliance_standard': 'Blue Drop Standards'
            },
            {
                'name': 'Social Impact Assessment',
                'description': 'Evaluate and improve community social impact programs',
                'category': 'Social',
                'priority': 'Medium',
                'compliance_standard': 'SLP Guidelines'
            },
            {
                'name': 'Energy Efficiency Audit',
                'description': 'Conduct energy efficiency assessment and implement improvements',
                'category': 'Environmental',
                'priority': 'Medium',
                'compliance_standard': 'Energy Efficiency Standards'
            },
            {
                'name': 'Local Procurement Policy',
                'description': 'Develop and implement local supplier development program',
                'category': 'Social',
                'priority': 'Medium',
                'compliance_standard': 'B-BBEE Codes'
            },
            {
                'name': 'Skills Development Program',
                'description': 'Establish employee training and development initiatives',
                'category': 'Social',
                'priority': 'High',
                'compliance_standard': 'Skills Development Act'
            },
            {
                'name': 'Waste Management System',
                'description': 'Implement comprehensive waste reduction and recycling program',
                'category': 'Environmental',
                'priority': 'High',
                'compliance_standard': 'National Waste Management Strategy'
            },
            {
                'name': 'Corporate Governance Framework',
                'description': 'Establish transparent governance and reporting structures',
                'category': 'Governance',
                'priority': 'High',
                'compliance_standard': 'King IV Code'
            },
            {
                'name': 'Stakeholder Engagement Plan',
                'description': 'Develop structured community and stakeholder engagement process',
                'category': 'Social',
                'priority': 'Medium',
                'compliance_standard': 'IFC Performance Standards'
            }
        ]
        
        created_measures = []
        for measure_data in measures_data:
            measure = Measure(
                name=measure_data['name'],
                description=measure_data['description'],
                category=measure_data['category'],
                priority=measure_data['priority'],
                compliance_standard=measure_data.get('compliance_standard'),
                created_at=datetime.utcnow(),
                created_by=admin.id
            )
            db.session.add(measure)
            created_measures.append(measure)
            print(f"✅ Measure created: {measure_data['name']}")
        
        db.session.flush()  # Get measure IDs
        
        # Create sample assignments for companies
        companies = Company.query.all()
        if companies and created_measures:
            for i, company in enumerate(companies):
                # Assign 3-4 measures to each company
                measures_to_assign = created_measures[i*3:(i+1)*3+1]
                
                for j, measure in enumerate(measures_to_assign):
                    assignment = MeasureAssignment(
                        company_id=company.id,
                        measure_id=measure.id,
                        status='Not Started' if j % 3 == 0 else ('In Progress' if j % 3 == 1 else 'Needs Assistance'),
                        assigned_date=datetime.utcnow(),
                        due_date=datetime.utcnow() + timedelta(days=30 + (j*15)),
                        urgency=min(j + 1, 3),
                        assigned_by=admin.id
                    )
                    db.session.add(assignment)
                    print(f"✅ Assignment created: {company.name} -> {measure.name}")
        
        # Commit all changes
        db.session.commit()
        
        # Check for and import original data
        original_data = load_original_data()
        if original_data:
            print("\n🔄 Found original data export, importing...")
            seed_original_data(original_data)
            db.session.commit()
            print("✅ Original data imported successfully!")
        else:
            print("\n💡 No original data export found, using sample data only")
        
        print("\n🎉 Database seeding completed successfully!")
        print("\n📋 Login Credentials:")
        print("=" * 50)
        print("🔧 ADMIN LOGIN:")
        print("   Email: admin@ptsa.com")
        print("   Password: admin123")
        print("\n🏢 COMPANY LOGINS:")
        
        # Show actual companies in database
        all_companies = Company.query.all()
        all_users = User.query.filter_by(role='company').all()
        
        if original_data:
            print("   📥 FROM ORIGINAL DATA:")
            for user in all_users:
                if user.company:
                    print(f"   Company: {user.company.name}")
                    print(f"   Email: {user.email}")
                    print("   Password: [Original password hash - unchanged]")
                    print()
        
        print("   📋 SAMPLE/TEST DATA:")
        for company_data in companies_data:
            print(f"   Company: {company_data['name']}")
            print(f"   Email: {company_data['email']}")
            print(f"   Password: {company_data['password']}")
            print()

def load_original_data():
    """Load original data if export file exists"""
    export_file = Path('original_data_export.json')
    if export_file.exists():
        with open(export_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def seed_original_data(original_data):
    """Seed database with original exported data"""
    
    print("🔄 Importing original data...")
    
    # Get admin user
    admin = User.query.filter_by(email='admin@ptsa.com').first()
    
    # Import original companies from the 'companies' table
    original_companies = original_data.get('tables', {}).get('companies', [])
    for company_data in original_companies:
        existing_company = Company.query.filter_by(name=company_data['name']).first()
        if not existing_company:
            company = Company(
                name=company_data['name'],
                region=company_data.get('region', 'South Africa'),
                industry_category=company_data.get('industry_category', 'Unknown'),
                created_at=datetime.fromisoformat(company_data['created_at']) if company_data.get('created_at') else datetime.utcnow()
            )
            # Preserve original ID mapping
            if 'id' in company_data:
                company.id = company_data['id']
            db.session.add(company)
            print(f"✅ Imported company: {company_data['name']}")
    
    db.session.flush()  # Get company IDs
    
    # Import original users from the 'users' table (excluding admin which we already created)
    original_users = original_data.get('tables', {}).get('users', [])
    for user_data in original_users:
        if user_data.get('email') != 'admin@ptsa.com':  # Skip admin, we already created it
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                # Find associated company by ID
                company = None
                if user_data.get('company_id'):
                    company = Company.query.filter_by(id=user_data['company_id']).first()
                
                user = User(
                    email=user_data['email'],
                    username=user_data.get('username', user_data['email'].split('@')[0]),
                    password_hash=user_data['password_hash'],
                    role=user_data.get('role', 'company'),
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    company_id=company.id if company else None,
                    is_active=user_data.get('is_active', True),
                    created_at=datetime.fromisoformat(user_data['created_at']) if user_data.get('created_at') else datetime.utcnow()
                )
                db.session.add(user)
                print(f"✅ Imported user: {user_data['email']} (Company: {company.name if company else 'None'})")
    
    db.session.flush()
    
    # Import original measures from the 'measures' table
    original_measures = original_data.get('tables', {}).get('measures', [])
    for measure_data in original_measures:
        existing_measure = Measure.query.filter_by(name=measure_data['name']).first()
        if not existing_measure:
            measure = Measure(
                name=measure_data['name'],
                description=measure_data.get('description', ''),
                category=measure_data.get('category', 'General'),
                priority=measure_data.get('priority', 'Medium'),
                compliance_standard=measure_data.get('compliance_standard'),
                created_at=datetime.fromisoformat(measure_data['created_at']) if measure_data.get('created_at') else datetime.utcnow(),
                created_by=admin.id
            )
            # Preserve original ID mapping
            if 'id' in measure_data:
                measure.id = measure_data['id']
            db.session.add(measure)
            print(f"✅ Imported measure: {measure_data['name']}")
    
    db.session.flush()
    
    # Import original measure assignments from the 'measure_assignments' table
    original_assignments = original_data.get('tables', {}).get('measure_assignments', [])
    for assignment_data in original_assignments:
        company = Company.query.filter_by(id=assignment_data.get('company_id')).first()
        measure = Measure.query.filter_by(id=assignment_data.get('measure_id')).first()
        
        if company and measure:
            existing_assignment = MeasureAssignment.query.filter_by(
                company_id=company.id, 
                measure_id=measure.id
            ).first()
            
            if not existing_assignment:
                assignment = MeasureAssignment(
                    company_id=company.id,
                    measure_id=measure.id,
                    status=assignment_data.get('status', 'Not Started'),
                    assigned_date=datetime.fromisoformat(assignment_data['assigned_date']) if assignment_data.get('assigned_date') else datetime.utcnow(),
                    due_date=datetime.fromisoformat(assignment_data['due_date']) if assignment_data.get('due_date') else None,
                    urgency=assignment_data.get('urgency', 1),
                    assigned_by=admin.id
                )
                db.session.add(assignment)
                print(f"✅ Imported assignment: {company.name} -> {measure.name}")
    
    # Note: We could also import assignment_steps, notifications, etc. if needed
    # For now, focusing on core data
    
    print("🎉 Original data import completed!")

if __name__ == '__main__':
    try:
        seed_database()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()