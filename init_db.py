#!/usr/bin/env python3
"""
Simple database initialization script for Render deployment
"""
import os
import sys
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User, Company, NotificationConfig
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with basic data"""
    print("🚀 Initializing database...")
    
    # Ensure instance directory exists
    instance_dir = Path("/app/instance")
    instance_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Instance directory: {instance_dir} (exists: {instance_dir.exists()})")
    
    app = create_app('production')
    print(f"🔧 Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        admin = User.query.filter_by(email='info@ptsa.co.za').first()
        if not admin:
            # Create admin user
            admin = User(
                email='info@ptsa.co.za',
                password=generate_password_hash('info123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            print("✅ Admin user created: info@ptsa.co.za / info123")
        else:
            print("ℹ️ Admin user already exists")
        
        # Create notification config if not exists
        config = NotificationConfig.query.first()
        if not config:
            config = NotificationConfig(
                lead_days=7,
                send_hour_utc=8,
                send_minute_utc=0
            )
            db.session.add(config)
            print("✅ Notification configuration created")
        
        # Commit all changes
        db.session.commit()
        print("✅ Database initialization completed!")

if __name__ == '__main__':
    init_database()
