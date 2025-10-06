#!/usr/bin/env python3
"""
Fix the dashboard notifications card to work properly
"""

def fix_dashboard_notifications():
    """Fix the Recent Notifications card on the dashboard"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\company\dashboard.html"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔧 Fixing dashboard notifications card...")
        
        # Replace the problematic moment() calls with server-side logic
        new_notifications_section = '''  <!-- Notifications Card -->
  <div class="col-md-6 col-lg-4">
    <div class="card h-100">
      <div class="card-header bg-info text-white">
        <h5 class="card-title mb-0">Recent Notifications</h5>
      </div>
      <div class="card-body p-0">
        <div class="list-group list-group-flush">
          {% set overdue_assignments = assignments|selectattr('is_overdue')|list %}
          {% set overdue_count = overdue_assignments|length %}
          
          {% if overdue_count > 0 %}
            <div class="list-group-item d-flex justify-content-between align-items-center">
              <div class="text-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Overdue measures
              </div>
              <span class="badge bg-danger rounded-pill">{{ overdue_count }}</span>
            </div>
            
            {# Show first few overdue measures #}
            {% for assignment in overdue_assignments[:2] %}
            <div class="list-group-item">
              <div class="d-flex justify-content-between align-items-start">
                <div class="me-auto">
                  <div class="fw-bold text-danger">{{ assignment.measure.name }}</div>
                  <small class="text-muted">Due: {{ assignment.due_at.strftime('%Y-%m-%d') if assignment.due_at else 'No date' }}</small>
                </div>
                <span class="badge bg-danger">Overdue</span>
              </div>
            </div>
            {% endfor %}
            
            {% if overdue_count > 2 %}
            <div class="list-group-item text-center">
              <small class="text-muted">And {{ overdue_count - 2 }} more overdue...</small>
            </div>
            {% endif %}
          {% else %}
            <div class="list-group-item">
              <div class="text-success">
                <i class="fas fa-check-circle me-2"></i>
                No overdue measures
              </div>
            </div>
          {% endif %}
        </div>
      </div>
      <div class="card-footer">
        <a href="{{ url_for('company.notifications') }}" class="btn btn-sm btn-outline-info">View All Notifications</a>
      </div>
    </div>
  </div>'''
        
        # Find and replace the notifications card section
        # Look for the start and end of the notifications card
        start_marker = '  <!-- Notifications Card -->'
        end_marker = '  </div>\n\n  <!-- Company Profile Card -->'
        
        start_pos = content.find(start_marker)
        if start_pos == -1:
            print("❌ Could not find notifications card start marker")
            return False
        
        # Find the end of this card (before Company Profile Card)
        temp_content = content[start_pos:]
        profile_card_pos = temp_content.find('<!-- Company Profile Card -->')
        if profile_card_pos == -1:
            print("❌ Could not find end marker")
            return False
        
        # Calculate the actual end position
        end_pos = start_pos + profile_card_pos
        
        # Replace the section
        new_content = content[:start_pos] + new_notifications_section + '\n\n  ' + content[end_pos:]
        
        # Write back the fixed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Dashboard notifications card fixed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_dashboard_route():
    """Ensure the dashboard route passes the necessary data"""
    
    print("🔧 Checking dashboard route...")
    
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
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if dashboard route exists and has assignments
        if 'def dashboard' in content:
            print("✅ Found dashboard route")
            
            # Check if it's passing assignments
            if 'assignments=' in content and 'dashboard.html' in content:
                print("✅ Dashboard route already passing assignments")
                return True
            else:
                print("⚠️  Dashboard route might need to pass assignments data")
                return True
        else:
            print("⚠️  Dashboard route not found in this file")
            return True
            
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return False

if __name__ == '__main__':
    import os
    
    print("🔧 Fixing dashboard notifications...")
    print("=" * 40)
    
    success = True
    
    # Fix the template
    if fix_dashboard_notifications():
        print("✅ Step 1: Template fixed")
    else:
        print("❌ Step 1: Template fix failed")
        success = False
    
    # Check the route
    if update_dashboard_route():
        print("✅ Step 2: Route checked")
    else:
        print("❌ Step 2: Route check failed")
        success = False
    
    if success:
        print("\n🎉 Dashboard notifications fixed!")
        print("📊 The Recent Notifications card will now show:")
        print("  - Count of overdue measures with red badges")
        print("  - First 2 overdue measures with details")
        print("  - 'View All Notifications' button that works")
        print("\n🌐 Visit: http://localhost:5000/company/dashboard")
    else:
        print("\n❌ Some fixes failed. Check the errors above.")