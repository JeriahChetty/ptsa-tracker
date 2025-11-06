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
        # Run Flask-Migrate migrations
        from flask_migrate import upgrade as flask_upgrade
        import os
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        try:
            logger.info(f"Running migrations from: {migrations_dir}")
            flask_upgrade(directory=migrations_dir)
            logger.info("✓ Database migrations applied")
        except Exception as migrate_error:
            logger.warning(f"Migration error: {migrate_error}")
            # Fallback to create_all if migrations fail
            db.create_all()
            logger.info("✓ Database tables created/verified (fallback)")
        
        # Ensure order column exists (fallback for migration issues)
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('measure_assignments')]
            if 'order' not in columns:
                logger.warning("⚠️  'order' column missing from measure_assignments, adding it now...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE measure_assignments ADD COLUMN \"order\" INTEGER DEFAULT 0"))
                    conn.commit()
                logger.info("✓ Added 'order' column to measure_assignments")
            else:
                logger.info("✓ 'order' column exists in measure_assignments")
        except Exception as col_error:
            logger.error(f"Error checking/adding order column: {col_error}")
        
        # Create default admin if needed
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        # Create default admin user if none exists
        admin = User.query.filter_by(email='info@ptsa.co.za').first()
        if not admin:
            admin = User(
                email='info@ptsa.co.za',
                password=generate_password_hash('info123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("✓ Default admin user created: info@ptsa.co.za")
        else:
            logger.info(f"✓ Admin user exists: {admin.email}")
            
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        # Don't crash - let the app try to run anyway

# Make sure the app is available for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

