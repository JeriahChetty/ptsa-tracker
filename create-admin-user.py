#!/usr/bin/env python3
"""Create admin user if it doesn't exist"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app import create_app
    from app.models import User, db
    from werkzeug.security import generate_password_hash
    
    print("🔧 Creating admin user...")
    
    # Create app with production config
    app = create_app()
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Check if admin exists
        existing_admin = User.query.filter_by(email='info@ptsa.co.za').first()
        if existing_admin:
            print("✅ Admin user info@ptsa.co.za already exists")
            print("🔐 You can login with: info@ptsa.co.za / info123")
        else:
            # Create admin user
            admin = User(
                email='info@ptsa.co.za',
                password=generate_password_hash('info123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("🔐 Login with: info@ptsa.co.za / info123")
            print(f"🌐 Access: https://ptsa-tracker.azurewebsites.net")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 This means either:")
    print("   1. Database is not accessible")
    print("   2. App is not properly configured")
    print("   3. Need to run full deployment")
    sys.exit(1)
