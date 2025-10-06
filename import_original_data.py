import json
from pathlib import Path
from datetime import datetime

# Import your database models and session
from models.py import Company, User, Measure, Assignment  # Use relative import if in a package
# or, if models.py is in the same directory:
# from models import Company, User, Measure, Assignment
# or, if models.py is in a subfolder named 'ptsa_tracker':
# from ptsa_tracker.models import Company, User, Measure, Assignment
from app import db  # Adjust the import path as needed

# Get the admin user (ensure this matches your actual admin creation logic)
admin = User.query.filter_by(email='admin@ptsa.com').first()

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
    
    # Import original companies
    for company_data in original_data.get('companies', []):
        existing_company = Company.query.filter_by(name=company_data['name']).first()
        if not existing_company:
            company = Company(
                name=company_data['name'],
                region=company_data.get('region', 'South Africa'),
                industry_category=company_data.get('industry_category', 'Unknown'),
                created_at=datetime.fromisoformat(company_data['created_at']) if company_data.get('created_at') else datetime.utcnow()
            )
            db.session.add(company)
            print(f"✅ Imported company: {company_data['name']}")
    
    db.session.flush()  # Get company IDs
    
    # Import original users (excluding admin which we already created)
    for user_data in original_data.get('users', []):
        if user_data.get('email') != 'admin@ptsa.com':  # Skip admin, we already created it
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                # Find associated company
                company = None
                if user_data.get('company_id'):
                    # Try to find company by original data
                    company_name = None
                    for comp in original_data.get('companies', []):
                        if comp.get('id') == user_data['company_id']:
                            company_name = comp['name']
                            break
                    if company_name:
                        company = Company.query.filter_by(name=company_name).first()
                
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
                print(f"✅ Imported user: {user_data['email']}")
    
    db.session.flush()
    
    # Import original measures
    for measure_data in original_data.get('measures', []):
        existing_measure = Measure.query.filter_by(name=measure_data['name']).first()
        if not existing_measure:
            measure = Measure(
                name=measure_data['name'],
                description=measure_data.get('description', ''),
                category=measure_data.get('category', 'General'),
                priority=measure_data.get('priority', 'Medium'),
                compliance_standard=measure_data.get('compliance_standard'),
                created_at=datetime.fromisoformat(measure_data['created_at']) if measure_data.get('created_at') else datetime.utcnow(),
                created_by=admin.id  # Use current admin as creator
            )
            db.session.add(measure)
            print(f"✅ Imported measure: {measure_data['name']}")
    
    db.session.flush()
    
    # Import original assignments
    for assignment_data in original_data.get('assignments', []):
        # Find corresponding company and measure
        company = None
        measure = None
        
        # Find company by original data
        for comp_data in original_data.get('companies', []):
            if comp_data.get('id') == assignment_data.get('company_id'):
                company = Company.query.filter_by(name=comp_data['name']).first()
                break
        
        # Find measure by original data  
        for measure_data in original_data.get('measures', []):
            if measure_data.get('id') == assignment_data.get('measure_id'):
                measure = Measure.query.filter_by(name=measure_data['name']).first()
                break
        
        if company and measure:
            existing_assignment = Assignment.query.filter_by(
                company_id=company.id, 
                measure_id=measure.id
            ).first()
            
            if not existing_assignment:
                assignment = Assignment(
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
    
    print("🎉 Original data import completed!")