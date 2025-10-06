# seed_admin.py
import os
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db           # <- use the SINGLE shared instance

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ptsa.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")

def main():
    app = create_app()
    with app.app_context():
        from app.models import User             # <- Import inside app context
        # (Optional) ensure tables exist if you're using SQLite in dev
        # If you're using Alembic migrations, you can keep this line or remove it.
        db.create_all()

        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if admin:
            print(f"[seed_admin] Admin already exists: {ADMIN_EMAIL}")
            return

        admin = User(
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            company_id=None,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"[seed_admin] ✅ Created admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

if __name__ == "__main__":
    main()


