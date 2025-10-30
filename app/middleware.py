from datetime import datetime, timedelta
from flask import request, redirect, url_for, session
from flask_login import current_user

def setup_session_protection(app):
    @app.before_request
    def check_session_expiration():
        # Skip for static files, auth endpoints, and health checks
        if (request.path.startswith('/static') or 
            request.path.startswith('/auth/') or
            request.path.startswith('/health')):
            return None
            
        # Check if user is logged in but session might be stale
        if current_user.is_authenticated:
            # Get last activity time
            last_activity_str = session.get('last_activity')
            
            # If no activity recorded, set it now and allow access
            if not last_activity_str:
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
                app.logger.info(f"Session initialized for user: {current_user.email}")
                return None
                
            try:
                # Parse the timestamp
                last_activity = datetime.fromisoformat(last_activity_str)
                
                # Check if session is too old (optional, as we use permanent sessions)
                max_idle = app.config.get('MAX_SESSION_IDLE_MINUTES', 240)  # Default 4 hours
                idle_duration = datetime.utcnow() - last_activity
                
                if idle_duration > timedelta(minutes=max_idle):
                    app.logger.warning(f"Session expired for user: {current_user.email} after {idle_duration}")
                    session.clear()
                    return redirect(url_for('auth.login', next=request.url))
                    
                # Update the timestamp for active users
                session['last_activity'] = datetime.utcnow().isoformat()
                session.modified = True
            except Exception as e:
                # If timestamp is invalid, reset it and allow access
                app.logger.warning(f"Session timestamp error: {e}, resetting for {current_user.email}")
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
