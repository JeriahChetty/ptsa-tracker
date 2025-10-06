from functools import wraps
from flask import session, redirect, url_for, request

# Make sure your login_required decorator or middleware is consistent
# Check if session timeout is too short
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # This is redirecting you to login
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function