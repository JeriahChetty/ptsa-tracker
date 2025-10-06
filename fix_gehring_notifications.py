#!/usr/bin/env python3
"""
Direct fix for company notifications to include overdue measures
"""

import sys
import os

def fix_company_notifications():
    """Directly fix the company notifications route"""
    
    print("🔧 Fixing company notifications route...")
    
    # Find the company routes file
    possible_files = [
        r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes\company_routes.py",
        r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\company_routes.py"
    ]
    
    routes_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            routes_file = file_path
            break
    
    if not routes_file:
        print("❌ Could not find company routes file!")
        return False
    
    print(f"📂 Found routes file: {routes_file}")
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if notifications route exists
        if 'def notifications' not in content:
            print("❌ No notifications route found!")
            return False
        
        # Add the overdue measures functionality
        overdue_code = '''
def get_overdue_assignments_for_company(company_id):
    """Get all overdue assignments for a company"""
    from datetime import datetime
    current_time = datetime.utcnow()
    
    overdue = MeasureAssignment.query.filter(
        MeasureAssignment.company_id == company_id,
        MeasureAssignment.due_at < current_time,
        MeasureAssignment.status.in_(['Not Started', 'In Progress', 'Needs Assistance'])
    ).order_by(MeasureAssignment.due_at.asc()).all()
    
    return overdue
'''
        
        # Find a good place to add the function (after imports, before routes)
        lines = content.split('\n')
        
        # Add the helper function if it doesn't exist
        if 'get_overdue_assignments_for_company' not in content:
            # Find where to insert (after imports, before first route)
            insert_line = 0
            for i, line in enumerate(lines):
                if line.startswith('@') and 'route' in line:
                    insert_line = i
                    break
            
            if insert_line > 0:
                function_lines = overdue_code.strip().split('\n')
                for j, func_line in enumerate(function_lines):
                    lines.insert(insert_line + j, func_line)
                
                print("✅ Added overdue assignments helper function")
        
        # Now update the notifications route
        content = '\n'.join(lines)
        lines = content.split('\n')
        
        # Find the notifications route and enhance it
        in_notifications = False
        render_line = -1
        
        for i, line in enumerate(lines):
            if 'def notifications' in line:
                in_notifications = True
            elif in_notifications and 'render_template' in line and 'notifications' in line:
                render_line = i
                break
        
        if render_line != -1:
            # Add overdue logic before render_template
            enhancement = [
                '    # Get overdue measures for this company',
                '    overdue_assignments = get_overdue_assignments_for_company(current_user.company.id)',
                '    ',
                '    # Create overdue notification objects',
                '    overdue_notifications = []',
                '    for assignment in overdue_assignments:',
                '        overdue_notifications.append({',
                '            "id": f"overdue_{assignment.id}",',
                '            "title": f"Overdue: {assignment.measure.name}",',
                '            "assignment": assignment,',
                '            "due_at": assignment.due_at,',
                '            "type": "overdue"',
                '        })',
                '    ',
                '    # Combine all notifications',
                '    all_notifications = list(notifications) + overdue_notifications',
                '    '
            ]
            
            # Insert enhancement before render_template
            for j, enh_line in enumerate(enhancement):
                lines.insert(render_line + j, enh_line)
            
            # Update render_template to use all_notifications
            render_line_new = render_line + len(enhancement)
            if 'notifications=' in lines[render_line_new]:
                lines[render_line_new] = lines[render_line_new].replace(
                    'notifications=notifications',
                    'notifications=all_notifications'
                )
            
            print("✅ Enhanced notifications route with overdue measures")
        
        # Write back the updated content
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("✅ Company routes updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating routes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 Applying direct fix for company notifications...")
    
    if fix_company_notifications():
        print("\n✅ Fix applied successfully!")
        print("🔄 Restart your Flask app and check notifications")
        print("🌐 Visit: http://localhost:5000/company/notifications")
    else:
        print("\n❌ Fix failed. Check errors above.")