from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - redirect based on user role."""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'company':
            return redirect(url_for('company.dashboard'))
    
    # Not authenticated - show login page
    return redirect(url_for('auth.login'))

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connectivity
        from app.extensions import db
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
