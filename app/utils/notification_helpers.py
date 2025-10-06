"""
Notification helper functions for PTSA Tracker
"""


def get_overdue_measures_for_company(company_id):
    """Get all overdue measures for a specific company"""
    from datetime import datetime
    from app.models import MeasureAssignment
    
    overdue_assignments = MeasureAssignment.query.filter(
        MeasureAssignment.company_id == company_id,
        MeasureAssignment.due_at < datetime.utcnow(),
        MeasureAssignment.status.in_(['Not Started', 'In Progress', 'Needs Assistance'])
    ).order_by(MeasureAssignment.due_at.asc()).all()
    
    return overdue_assignments

def create_overdue_notifications(company_id):
    """Create notification objects for overdue measures"""
    from datetime import datetime
    
    overdue_assignments = get_overdue_measures_for_company(company_id)
    notifications = []
    
    for assignment in overdue_assignments:
        # Create a notification-like object
        notification = {
            'id': f"overdue_{assignment.id}",
            'title': f"Overdue: {assignment.measure.name}",
            'message': f"This measure was due on {assignment.due_at.strftime('%Y-%m-%d')}",
            'type': 'overdue',
            'assignment': assignment,
            'due_at': assignment.due_at,
            'created_at': datetime.utcnow(),
            'is_read': False
        }
        notifications.append(notification)
    
    return notifications
