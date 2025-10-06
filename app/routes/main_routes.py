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
    """Health check endpoint for container monitoring."""
    return {"status": "healthy", "app": "PTSA Tracker"}, 200
