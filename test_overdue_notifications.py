#!/usr/bin/env python3
"""
Test script for overdue notifications
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_overdue_notifications():
    """Test the overdue notifications functionality"""
    
    print("🧪 Testing overdue notifications...")
    
    try:
        from app import create_app, db
        from app.models import Company, MeasureAssignment
        from app.utils.notification_helpers import get_overdue_measures_for_company, create_overdue_notifications
        from datetime import datetime, timedelta
        
        app = create_app()
        
        with app.app_context():
            # Get first company
            company = Company.query.first()
            if not company:
                print("❌ No companies found for testing")
                return False
            
            print(f"📊 Testing with company: {company.name}")
            
            # Check for overdue measures
            overdue_assignments = get_overdue_measures_for_company(company.id)
            print(f"📅 Found {len(overdue_assignments)} overdue assignments")
            
            if overdue_assignments:
                for assignment in overdue_assignments:
                    days_overdue = (datetime.utcnow().date() - assignment.due_at.date()).days
                    print(f"  - {assignment.measure.name}: {days_overdue} days overdue")
            
            # Create notification objects
            notifications = create_overdue_notifications(company.id)
            print(f"🔔 Created {len(notifications)} overdue notifications")
            
            # Show sample notifications
            for notif in notifications[:3]:  # Show first 3
                print(f"  📬 {notif['title']}")
                print(f"     Due: {notif['due_at'].strftime('%Y-%m-%d')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_overdue_notifications()
