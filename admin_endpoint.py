#!/usr/bin/env python3
"""
Quick admin creation via web endpoint
"""

from flask import Flask
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin_endpoint():
    app = create_app()
    
    @app.route('/create-admin-now')
    def create_admin_now():
        try:
            with app.app_context():
                db.create_all()
                
                # Delete existing admin if any
                existing_admin = User.query.filter_by(email='admin@ptsa.com').first()
                if existing_admin:
                    db.session.delete(existing_admin)
                    db.session.commit()
                
                # Create fresh admin user
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
                
                return 'Admin user created successfully! Email: admin@ptsa.com, Password: admin123'
        except Exception as e:
            return f'Error: {str(e)}'
    
    return app

if __name__ == '__main__':
    app = create_admin_endpoint()
    app.run(debug=True)