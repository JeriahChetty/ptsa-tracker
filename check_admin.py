#!/usr/bin/env python3
"""
Check and create admin user in Azure container
"""

from app import create_app, db
from app.models import User, Company
from werkzeug.security import generate_password_hash

def check_and_create_admin():
    app = create_app()
    with app.app_context():
        # Check existing users
        users = User.query.all()
        print(f'Total users: {len(users)}')
        for user in users:
            print(f'Email: {user.email}, Role: {user.role}')
        
        # Check for admin
        admin = User.query.filter_by(email='admin@ptsa.com').first()
        if admin:
            print('✅ Admin user exists')
            # Reset password just in case
            admin.password_hash = generate_password_hash('admin123')
            db.session.commit()
            print('✅ Admin password reset to: admin123')
        else:
            print('❌ Admin user NOT found - creating now...')
            admin = User(
                email='admin@ptsa.com',
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                first_name='System',
                last_name='Administrator',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin user created successfully!')
        
        # Check companies
        companies = Company.query.all()
        print(f'\nCompanies: {len(companies)}')
        for company in companies[:5]:  # Show first 5
            print(f'- {company.name}')
        
        # Check company users
        company_users = User.query.filter_by(role='company').all()
        print(f'\nCompany users: {len(company_users)}')
        for user in company_users[:3]:  # Show first 3
            print(f'- {user.email}')

if __name__ == '__main__':
    check_and_create_admin()