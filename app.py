from datetime import timedelta
from flask import Flask
from werkzeug.security import generate_password_hash
from app import db
from app.models import User

# Create Flask app
app = Flask(__name__)

# Increase session lifetime if it's too short
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)  # Adjust as needed
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

@app.route('/create-admin-now')
def create_admin_now():
    try:
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

# Create the fresh admin user route
@app.route('/create-admin')
def create_admin():
    try:
        # Delete existing admin users to prevent duplicates
        existing_admins = User.query.filter_by(role='admin').all()
        for admin in existing_admins:
            db.session.delete(admin)
            db.session.commit()

        # Create fresh admin user
        admin = User(
            email='admin@ptsa.co.za',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            first_name='System',
            last_name='Administrator',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

        return 'Admin user created successfully! Email: admin@ptsa.co.za, Password: admin123'
    except Exception as e:
        return f'Error: {str(e)}'

# Add the main block for proper container deployment
if __name__ == '__main__':
    # Import here to avoid circular imports
    from app import create_app
    from app.extensions import db
    
    # Create the Flask app instance
    app = create_app('production')
    
    # Initialize the database within app context
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
            
            # Create default admin user if none exists
            from app.models import User
            from werkzeug.security import generate_password_hash
            
            # Check for existing admin users
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                # Create admin user with the correct field name
                admin = User(
                    email='admin@ptsa.co.za',
                    password=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Default admin user created:")
                print("  Email: admin@ptsa.co.za")
                print("  Password: admin123")
            else:
                print("Admin user already exists:")
                print(f"  Email: {admin_exists.email}")
                print(f"  Role: {admin_exists.role}")
                print(f"  Active: {admin_exists.is_active}")
                
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    # Get port from environment or default to 5000
    import os
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"Starting Flask app on {host}:{port}")
    print("Environment:", os.environ.get('FLASK_ENV', 'development'))
    
    # Run the app with container-friendly settings
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False  # Important for container deployment
    )