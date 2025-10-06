#!/usr/bin/env python3
"""
Fix the notifications template to work without moment() dependency
"""

def fix_notifications_template():
    """Replace the problematic moment() calls with server-side logic"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\company\notifications.html"
    
    # Create a simplified, working template
    new_template = '''{% extends "base.html" %}
{% block title %}Notifications · PTSA Tracker{% endblock %}

{% block head %}
  {{ super() }}
  <style>
    .countdown-timer {
      font-weight: bold;
      font-size: 0.9em;
    }
    .overdue { color: #dc3545; }
    .due-soon { color: #fd7e14; }
    .due-later { color: #198754; }
    .overdue-badge { background-color: #dc3545; }
    .due-soon-badge { background-color: #fd7e14; }
    .due-later-badge { background-color: #198754; }
  </style>
{% endblock %}

{% block content %}
<h1 class="h4 mb-3">Notifications</h1>

{% set items = notifications or [] %}

{% if not items %}
  <div class="alert alert-info">
    <i class="fas fa-info-circle me-2"></i>
    No notifications right now.
  </div>
{% else %}
  {# All notifications - we'll separate them by type #}
  {% set overdue_items = items | selectattr('type', 'equalto', 'overdue') | list %}
  {% set other_items = items | rejectattr('type', 'equalto', 'overdue') | list %}

  {# Overdue Measures Section #}
  {% if overdue_items %}
  <div class="card border-danger mb-4">
    <div class="card-header bg-danger text-white">
      <h5 class="mb-0">
        <i class="fas fa-exclamation-triangle me-2"></i>
        Overdue Measures ({{ overdue_items|length }})
      </h5>
    </div>
    <div class="card-body p-0">
      <ul class="list-group list-group-flush" role="list">
        {% for n in overdue_items %}
          <li class="list-group-item d-flex justify-content-between align-items-start border-start border-danger border-3">
            <div class="me-3 flex-grow-1">
              <div class="fw-semibold">
                {{ n.title or (n.assignment.measure.name if n.assignment and n.assignment.measure else 'Measure') }}
              </div>
              <div class="small text-muted mb-1">
                {% if n.assignment and n.assignment.company %}
                  Company: {{ n.assignment.company.name }}
                {% endif %}
              </div>
              <div class="small">
                {% if n.due_at %}
                  <span class="badge overdue-badge">
                    <i class="fas fa-clock me-1"></i>
                    Overdue
                  </span>
                  <span class="text-muted ms-2">Due: {{ n.due_at.strftime('%Y-%m-%d') }}</span>
                {% else %}
                  <span class="badge bg-secondary">No due date</span>
                {% endif %}
              </div>
            </div>

            <div class="d-flex align-items-center gap-2">
              {% if n.assignment %}
                <a class="btn btn-sm btn-danger" 
                   href="{{ url_for('company.view_measure', measure_id=n.assignment.measure.id) }}" 
                   role="button" title="View measure">
                  <i class="fas fa-eye me-1"></i>View
                </a>
              {% else %}
                <a class="btn btn-sm btn-outline-danger" href="{{ url_for('company.dashboard') }}" role="button" title="Go to dashboard">
                  <i class="fas fa-tachometer-alt me-1"></i>Dashboard
                </a>
              {% endif %}

              {% if n.get('id') and n.id != n.get('id', '').startswith('overdue_') %}
              <form method="post" action="{{ url_for('company.mark_notification_read', notification_id=n.id) }}" class="d-inline">
                <button type="submit" class="btn btn-sm btn-outline-secondary" title="Mark as read">
                  <i class="fas fa-check"></i>
                </button>
              </form>
              {% endif %}
            </div>
          </li>
        {% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}

  {# Other Notifications Section #}
  {% if other_items %}
  <div class="card">
    <div class="card-header">
      <h5 class="mb-0">
        <i class="fas fa-bell me-2"></i>
        Other Notifications ({{ other_items|length }})
      </h5>
    </div>
    <div class="card-body p-0">
      <ul class="list-group list-group-flush" role="list">
        {% for n in other_items %}
          <li class="list-group-item d-flex justify-content-between align-items-start">
            <div class="me-3 flex-grow-1">
              <div class="fw-semibold">
                {{ n.title or (n.assignment.measure.name if n.assignment and n.assignment.measure else 'Notification') }}
              </div>
              <div class="small text-muted mb-1">
                {% if n.assignment and n.assignment.company %}
                  Company: {{ n.assignment.company.name }}
                {% endif %}
              </div>
              <div class="small">
                {% if n.due_at %}
                  <span class="badge bg-primary">
                    <i class="fas fa-calendar me-1"></i>
                    Due: {{ n.due_at.strftime('%Y-%m-%d') }}
                  </span>
                {% else %}
                  <span class="badge bg-secondary">No due date</span>
                {% endif %}
              </div>
            </div>

            <div class="d-flex align-items-center gap-2">
              {% if n.assignment %}
                <a class="btn btn-sm btn-outline-primary" 
                   href="{{ url_for('company.view_measure', measure_id=n.assignment.measure.id) }}" 
                   role="button" title="View measure">
                  <i class="fas fa-eye me-1"></i>View
                </a>
              {% else %}
                <a class="btn btn-sm btn-outline-primary" href="{{ url_for('company.dashboard') }}" role="button" title="Go to dashboard">
                  <i class="fas fa-tachometer-alt me-1"></i>Dashboard
                </a>
              {% endif %}

              {% if n.get('id') %}
              <form method="post" action="{{ url_for('company.mark_notification_read', notification_id=n.id) }}" class="d-inline">
                <button type="submit" class="btn btn-sm btn-outline-secondary" title="Mark as read">
                  <i class="fas fa-check"></i>
                </button>
              </form>
              {% endif %}
            </div>
          </li>
        {% endfor %}
      </ul>
    </div>
  </div>
  {% endif %}
{% endif %}
{% endblock %}
'''

    try:
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(new_template)
        
        print("✅ Fixed notifications template!")
        print("🔧 Removed moment() dependency")
        print("📱 Template now uses server-side date logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing template: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing notifications template...")
    
    if fix_notifications_template():
        print("\n✅ Template fixed successfully!")
        print("🔄 The notifications page should now work")
        print("🌐 Try visiting: http://localhost:5000/company/notifications")
    else:
        print("\n❌ Failed to fix template")