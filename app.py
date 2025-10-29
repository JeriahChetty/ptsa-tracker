#!/usr/bin/env python3
"""
Alternative entry point for PTSA Tracker
This file provides a direct way to run the app for development/debugging.
For production, use wsgi.py instead.
"""
import os
from app import create_app
from app.extensions import db

# Create the Flask app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Initialize the database within app context
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Create default admin user if none exists
            from app.models import User
            from werkzeug.security import generate_password_hash
            
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                admin = User(
                    email='admin@ptsa.co.za',
                    password=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("✓ Default admin user created:")
                print("  Email: admin@ptsa.co.za")
                print("  Password: admin123")
            else:
                print("✓ Admin user already exists:")
                print(f"  Email: {admin_exists.email}")
                
        except Exception as e:
            print(f"✗ Database initialization error: {e}")
    
    # Get configuration from environment
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n🚀 Starting PTSA Tracker on {host}:{port}")
    print(f"   Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"   Debug mode: {debug}\n")
    
    # Run the app
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )