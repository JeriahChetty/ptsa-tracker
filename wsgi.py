#!/usr/bin/env python3
"""
WSGI entry point for PTSA Tracker
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment to production
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask application factory
from app import create_app
from app.extensions import db

# Create the Flask application instance
app = create_app('production')

# Initialize database on startup
with app.app_context():
    try:
        # Create all tables if they don't exist
        db.create_all()
        logger.info("✓ Database tables created/verified")
        
        # Create default admin if needed
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count == 0:
            admin = User(
                email='admin@ptsa.co.za',
                password=generate_password_hash('admin123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("✓ Default admin user created")
        else:
            logger.info(f"✓ Found {admin_count} admin user(s)")
            
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        # Don't crash - let the app try to run anyway

# Make sure the app is available for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

