from datetime import datetime, timedelta
from flask import request, redirect, url_for, session
from flask_login import current_user

def setup_session_protection(app):
    @app.before_request
    def check_session_expiration():
        # Skip for static files and auth endpoints
        if request.path.startswith('/static') or request.path.startswith('/auth/'):
            return None
            
        # Check if user is logged in but session might be stale
        if current_user.is_authenticated:
            # Get last activity time
            last_activity_str = session.get('last_activity')
            
            # If no activity recorded, set it now
            if not last_activity_str:
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
                return None
                
            try:
                # Parse the timestamp
                last_activity = datetime.fromisoformat(last_activity_str)
                
                # Check if session is too old (optional, as we use permanent sessions)
                max_idle = app.config.get('MAX_SESSION_IDLE_MINUTES', 60)  # Default 1 hour
                if datetime.utcnow() - last_activity > timedelta(minutes=max_idle):
                    return redirect(url_for('auth.login', next=request.url))
                    
                # Update the timestamp for active users
                session['last_activity'] = datetime.utcnow().isoformat()
            except:
                # If timestamp is invalid, just update it
                session['last_activity'] = datetime.utcnow().isoformat()
