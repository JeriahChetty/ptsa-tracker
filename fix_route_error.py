#!/usr/bin/env python3
"""
Quick fix for the route error in notifications template
"""

def fix_route_error():
    """Fix the route error in notifications template"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\company\notifications.html"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔧 Fixing route errors...")
        
        # Replace the problematic route calls
        fixes = [
            # Fix view_assignment route that doesn't exist
            ("company.view_assignment", "company.view_measure"),
            ("admin.view_assignment", "admin.view_measure"),
            ("assignment_id=n.assignment.id", "measure_id=n.assignment.measure.id"),
            # Remove problematic role-based routing
            ('href="{{ url_for(\'admin.view_assignment\' if current_user.role == \'admin\' else \'company.view_assignment\', assignment_id=n.assignment.id) }}"',
             'href="{{ url_for(\'company.view_measure\', measure_id=n.assignment.measure.id) }}"'),
        ]
        
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                print(f"✅ Fixed: {old} -> {new}")
        
        # Write back the fixed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Template fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing template: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing route errors in notifications template...")
    
    if fix_route_error():
        print("\n✅ Route errors fixed!")
        print("🔄 Try visiting notifications page again")
        print("🌐 http://localhost:5000/company/notifications")
    else:
        print("\n❌ Failed to fix routes")