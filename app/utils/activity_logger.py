"""Activity logging utility for tracking user actions"""
import json
from flask import request
from flask_login import current_user
from app.extensions import db
from app.models import ActivityLog


def log_activity(action: str, entity_type: str = None, entity_id: int = None, 
                 entity_name: str = None, details: dict = None):
    """
    Log a user activity
    
    Args:
        action: The action performed (create, update, delete, login, logout, view, etc.)
        entity_type: Type of entity (measure, company, user, assignment, etc.)
        entity_id: ID of the entity
        entity_name: Name/title of the entity for reference
        details: Additional details as a dictionary
    """
    try:
        if not current_user.is_authenticated:
            return
        
        # Get IP and user agent
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        # Convert details to JSON string if provided
        details_json = json.dumps(details) if details else None
        
        # Create activity log
        activity = ActivityLog(
            user_id=current_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None  # Truncate if too long
        )
        
        db.session.add(activity)
        db.session.commit()
        
    except Exception as e:
        # Don't let logging errors break the application
        print(f"Error logging activity: {e}")
        db.session.rollback()


def log_login(user_email: str):
    """Log user login"""
    log_activity(
        action='login',
        entity_type='user',
        entity_name=user_email
    )


def log_logout(user_email: str):
    """Log user logout"""
    log_activity(
        action='logout',
        entity_type='user',
        entity_name=user_email
    )


def log_create(entity_type: str, entity_id: int, entity_name: str, details: dict = None):
    """Log entity creation"""
    log_activity(
        action='create',
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=details
    )


def log_update(entity_type: str, entity_id: int, entity_name: str, details: dict = None):
    """Log entity update"""
    log_activity(
        action='update',
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=details
    )


def log_delete(entity_type: str, entity_id: int, entity_name: str, details: dict = None):
    """Log entity deletion"""
    log_activity(
        action='delete',
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=details
    )


def log_view(entity_type: str, entity_id: int, entity_name: str):
    """Log entity view (optional, can be noisy)"""
    log_activity(
        action='view',
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name
    )
