from datetime import datetime, timedelta
from flask import request, redirect, url_for, session
from flask_login import current_user

def setup_session_protection(app):
    @app.before_request
    def check_session_expiration():
        try:
            # Skip for static files, auth endpoints, and health checks
            if (request.path.startswith('/static') or 
                request.path.startswith('/auth/') or
                request.path.startswith('/health')):
                return None
                
            # Check if user is logged in but session might be stale
            if not current_user.is_authenticated:
                return None
                
            # User is authenticated, check session
            # Get last activity time
            last_activity_str = session.get('last_activity')
            
            # If no activity recorded, set it now and allow access
            if not last_activity_str:
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
                # Safe logging - get email only if user is authenticated
                user_email = getattr(current_user, 'email', 'unknown')
                app.logger.info(f"Session initialized for user: {user_email}")
                return None
                
            try:
                # Parse the timestamp
                last_activity = datetime.fromisoformat(last_activity_str)
                
                # Check if session is too old (optional, as we use permanent sessions)
                max_idle = app.config.get('MAX_SESSION_IDLE_MINUTES', 240)  # Default 4 hours
                idle_duration = datetime.utcnow() - last_activity
                
                if idle_duration > timedelta(minutes=max_idle):
                    user_email = getattr(current_user, 'email', 'unknown')
                    app.logger.warning(f"Session expired for user: {user_email} after {idle_duration}")
                    session.clear()
                    return redirect(url_for('auth.login', next=request.url))
                    
                # Update the timestamp for active users
                session['last_activity'] = datetime.utcnow().isoformat()
                session.modified = True
            except Exception as e:
                # If timestamp is invalid, reset it and allow access
                user_email = getattr(current_user, 'email', 'unknown')
                app.logger.warning(f"Session timestamp error: {e}, resetting for {user_email}")
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
        except Exception as e:
            # Catch all errors in middleware to prevent crashes
            app.logger.error(f"Middleware error: {e}")
            return None  # Allow request to continue even if middleware fails
