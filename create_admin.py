#!/usr/bin/env python3
"""
Simple admin user creation script for Azure SQL Database
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@ptsa.com').first()
        if not admin:
            print('Creating admin user...')
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
            print('✅ Admin user created: admin@ptsa.com / admin123')
        else:
            print('✅ Admin user already exists')
            # Reset password to ensure it works
            admin.password_hash = generate_password_hash('admin123')
            db.session.commit()
            print('✅ Admin password reset: admin@ptsa.com / admin123')
            
        # Show all users for verification
        users = User.query.all()
        print(f'📊 Total users in database: {len(users)}')
        for user in users:
            print(f'  - {user.email} ({user.role})')

if __name__ == '__main__':
    create_admin()