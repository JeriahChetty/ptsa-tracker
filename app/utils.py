import os
from flask import url_for, flash, request, current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

ALLOWED = {'pdf','png','jpg','jpeg','webp'}

def allowed_file(fname: str) -> bool:
    return '.' in fname and fname.rsplit('.',1)[1].lower() in ALLOWED

def secure_join(base, *paths):
    path = os.path.join(base, *paths)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def safe_url_for(endpoint, **kwargs):
    """Generate a URL, but redirect unauthenticated users to login for protected endpoints."""
    # Protected endpoints that need authentication
    protected_prefixes = ['admin.', 'company.']
    
    # If trying to access protected endpoint but not logged in, go to login
    if not current_user.is_authenticated and any(endpoint.startswith(p) for p in protected_prefixes):
        return url_for('auth.login', next=url_for(endpoint, **kwargs))
    
    return url_for(endpoint, **kwargs)

# Error handling decorators
def handle_benchmarking_errors(f):
    """Decorator to handle common benchmarking operation errors."""
    from functools import wraps
    from flask import flash, redirect, request, url_for, current_app
    from sqlalchemy.exc import IntegrityError
    from app.extensions import db
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except IntegrityError as e:
            db.session.rollback()
            if "uq_company_benchmark_year" in str(e):
                flash("Benchmarking data for this year already exists.", "warning")
            else:
                flash("A database error occurred. Please try again.", "danger")
            return redirect(request.referrer or url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Benchmarking error: {str(e)}")
            flash("An unexpected error occurred. Please try again.", "danger")
            return redirect(request.referrer or url_for('admin.dashboard'))
    
    return decorated_function
