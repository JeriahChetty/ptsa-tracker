from flask import Blueprint, render_template, session
from flask_login import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required  # Make sure this decorator is applied
def dashboard():
    # Add debug logging to see what's happening
    print(f"User in session: {session.get('user_id')}")
    # ...dashboard logic...
    return render_template('admin/dashboard.html')

# Check that your /admin/measures/history route also has the login_required decorator
# if it should be protected
@admin_bp.route('/measures/history')
@login_required  # If this is missing but present on dashboard, it would explain the behavior
def measures_history():
    # ...history logic...
    return render_template('admin/measures_history.html')