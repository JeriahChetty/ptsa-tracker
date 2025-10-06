#!/usr/bin/env python3
"""
Add overdue measures notification functionality
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def add_overdue_notifications():
    """Add functionality to show overdue measures in notifications"""
    
    print("🔔 Setting up overdue measures notifications...")
    
    # 1. First, let's add a helper function to find overdue measures
    helper_code = '''
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
'''
    
    # Add to a utilities file
    utils_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\utils\notification_helpers.py"
    
    # Create utils directory if it doesn't exist
    utils_dir = os.path.dirname(utils_file)
    if not os.path.exists(utils_dir):
        os.makedirs(utils_dir)
        print(f"✅ Created utils directory: {utils_dir}")
        
        # Create __init__.py
        with open(os.path.join(utils_dir, '__init__.py'), 'w') as f:
            f.write('# Utils package\n')
    
    try:
        with open(utils_file, 'w', encoding='utf-8') as f:
            f.write(f'"""\nNotification helper functions for PTSA Tracker\n"""\n\n{helper_code}')
        
        print(f"✅ Created notification helpers: {utils_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating helpers: {e}")
        return False

def update_company_routes():
    """Update company routes to include overdue measures in notifications"""
    
    routes_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes\company_routes.py"
    
    if not os.path.exists(routes_file):
        # Try alternative location
        routes_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\company_routes.py"
    
    if not os.path.exists(routes_file):
        print("❌ Could not find company routes file")
        return False
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add import for our helper functions
        import_line = "from app.utils.notification_helpers import get_overdue_measures_for_company, create_overdue_notifications"
        
        if import_line not in content:
            # Find a good place to add the import
            lines = content.split('\n')
            import_added = False
            
            for i, line in enumerate(lines):
                if line.startswith('from app.models') or line.startswith('from app import'):
                    lines.insert(i + 1, import_line)
                    import_added = True
                    break
            
            if not import_added:
                # Add at the top after existing imports
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and not line.startswith('from') and not line.startswith('import'):
                        lines.insert(i, import_line)
                        break
            
            content = '\n'.join(lines)
            print("✅ Added import for notification helpers")
        
        # Now let's update the notifications route
        if 'def notifications' in content:
            print("✅ Found notifications route - will enhance it")
            
            # Add code to include overdue measures
            enhancement_code = '''
    # Get overdue measures for this company
    overdue_notifications = create_overdue_notifications(current_user.company.id)
    
    # Combine with existing notifications
    all_notifications = list(notifications) + overdue_notifications
    all_notifications.sort(key=lambda x: x.get('due_at') or x.get('created_at'), reverse=False)'''
            
            # Find the notifications function and enhance it
            lines = content.split('\n')
            in_notifications_func = False
            render_template_line = -1
            
            for i, line in enumerate(lines):
                if 'def notifications' in line:
                    in_notifications_func = True
                elif in_notifications_func and 'render_template' in line and 'notifications.html' in line:
                    render_template_line = i
                    break
            
            if render_template_line != -1:
                # Insert our code before the render_template call
                enhancement_lines = enhancement_code.strip().split('\n')
                for j, enh_line in enumerate(enhancement_lines):
                    lines.insert(render_template_line + j, '    ' + enh_line)
                
                # Update the render_template call to use all_notifications
                original_render = lines[render_template_line + len(enhancement_lines)]
                if 'notifications=' in original_render:
                    lines[render_template_line + len(enhancement_lines)] = original_render.replace(
                        'notifications=notifications', 
                        'notifications=all_notifications'
                    )
                
                content = '\n'.join(lines)
                print("✅ Enhanced notifications route with overdue measures")
        
        # Write back the updated content
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Updated company routes successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating routes: {e}")
        return False

def create_test_script():
    """Create a test script to verify overdue notifications work"""
    
    test_script = '''#!/usr/bin/env python3
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
'''
    
    test_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\test_overdue_notifications.py"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        print(f"✅ Created test script: {test_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test script: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Setting up overdue measures notifications...")
    print("=" * 50)
    
    success = True
    
    # Step 1: Create helper functions
    if add_overdue_notifications():
        print("✅ Step 1: Helper functions created")
    else:
        print("❌ Step 1: Failed to create helpers")
        success = False
    
    # Step 2: Update company routes
    if update_company_routes():
        print("✅ Step 2: Company routes updated")
    else:
        print("❌ Step 2: Failed to update routes")
        success = False
    
    # Step 3: Create test script
    if create_test_script():
        print("✅ Step 3: Test script created")
    else:
        print("❌ Step 3: Failed to create test script")
        success = False
    
    if success:
        print(f"\n🎉 Setup completed successfully!")
        print(f"📋 Next steps:")
        print(f"   1. Run: python test_overdue_notifications.py")
        print(f"   2. Check company notifications page")
        print(f"   3. Overdue measures will appear in red 'Overdue Measures' section")
    else:
        print(f"\n❌ Setup failed. Check the errors above.")
        sys.exit(1)