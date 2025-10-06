#!/usr/bin/env python3
"""
Diagnostic script to check why overdue measures aren't showing for Gehring
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def diagnose_gehring_overdue():
    """Diagnose overdue measures for Gehring company"""
    
    print("🔍 Diagnosing Gehring Company Overdue Measures")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.models import Company, MeasureAssignment
        from datetime import datetime
        
        app = create_app()
        
        with app.app_context():
            # Find Gehring company
            gehring = Company.query.filter(Company.name.ilike('%gehring%')).first()
            
            if not gehring:
                print("❌ Gehring company not found!")
                print("📋 Available companies:")
                companies = Company.query.all()
                for comp in companies:
                    print(f"  - {comp.name} (ID: {comp.id})")
                return False
            
            print(f"✅ Found company: {gehring.name} (ID: {gehring.id})")
            
            # Check all assignments for Gehring
            all_assignments = MeasureAssignment.query.filter_by(company_id=gehring.id).all()
            print(f"📊 Total assignments for Gehring: {len(all_assignments)}")
            
            if not all_assignments:
                print("❌ No assignments found for Gehring!")
                return False
            
            # Analyze each assignment
            now = datetime.utcnow()
            overdue_count = 0
            upcoming_count = 0
            no_due_date_count = 0
            completed_count = 0
            
            print(f"\n📅 Assignment Analysis (Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}):")
            print("-" * 80)
            
            for assignment in all_assignments:
                status = assignment.status or 'Not Started'
                due_date = assignment.due_at
                measure_name = assignment.measure.name if assignment.measure else 'Unknown'
                
                if status == 'Completed':
                    completed_count += 1
                    status_indicator = "✅"
                elif not due_date:
                    no_due_date_count += 1
                    status_indicator = "⚪"
                elif due_date < now:
                    overdue_count += 1
                    status_indicator = "🔴"
                else:
                    upcoming_count += 1
                    status_indicator = "🟡"
                
                days_diff = ""
                if due_date:
                    diff = (due_date - now).days
                    if diff < 0:
                        days_diff = f"({abs(diff)} days overdue)"
                    elif diff == 0:
                        days_diff = "(due today)"
                    else:
                        days_diff = f"({diff} days remaining)"
                
                print(f"{status_indicator} {measure_name}")
                print(f"   Status: {status}")
                print(f"   Due: {due_date.strftime('%Y-%m-%d %H:%M:%S') if due_date else 'No due date'} {days_diff}")
                print()
            
            # Summary
            print("📊 SUMMARY:")
            print(f"  🔴 Overdue: {overdue_count}")
            print(f"  🟡 Upcoming: {upcoming_count}")
            print(f"  ✅ Completed: {completed_count}")
            print(f"  ⚪ No due date: {no_due_date_count}")
            
            # Test the notification helper functions
            print(f"\n🔧 Testing notification helper functions...")
            
            try:
                # Try to import our helper functions
                from app.utils.notification_helpers import get_overdue_measures_for_company, create_overdue_notifications
                
                overdue_assignments = get_overdue_measures_for_company(gehring.id)
                print(f"✅ Helper function found {len(overdue_assignments)} overdue assignments")
                
                notifications = create_overdue_notifications(gehring.id)
                print(f"✅ Created {len(notifications)} notification objects")
                
                if notifications:
                    print(f"📬 Sample notifications:")
                    for notif in notifications[:3]:
                        print(f"  - {notif['title']}")
                        print(f"    Due: {notif['due_at'].strftime('%Y-%m-%d')}")
                        print(f"    Type: {notif['type']}")
                
            except ImportError as e:
                print(f"❌ Helper functions not found: {e}")
                print("   Run: python setup_overdue_notifications.py")
                
            except Exception as e:
                print(f"❌ Error with helper functions: {e}")
                import traceback
                traceback.print_exc()
            
            # Check if company routes are updated
            print(f"\n🔧 Checking company routes...")
            routes_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes\company_routes.py"
            
            if not os.path.exists(routes_file):
                routes_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\company_routes.py"
            
            if os.path.exists(routes_file):
                with open(routes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'notification_helpers' in content:
                    print("✅ Routes file has notification helpers import")
                else:
                    print("❌ Routes file missing notification helpers import")
                
                if 'create_overdue_notifications' in content:
                    print("✅ Routes file uses overdue notification function")
                else:
                    print("❌ Routes file not calling overdue notification function")
            else:
                print("❌ Company routes file not found")
            
            return overdue_count > 0
            
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_fix_for_gehring():
    """Quick fix to ensure Gehring's overdue measures show up"""
    
    print(f"\n🔧 Applying quick fix for Gehring...")
    
    try:
        # Create a simple notification test
        routes_content = '''
# Quick fix for overdue notifications - add to company routes

def get_company_overdue_assignments(company_id):
    """Get overdue assignments for a company"""
    from datetime import datetime
    from app.models import MeasureAssignment
    
    return MeasureAssignment.query.filter(
        MeasureAssignment.company_id == company_id,
        MeasureAssignment.due_at < datetime.utcnow(),
        MeasureAssignment.status.in_(['Not Started', 'In Progress', 'Needs Assistance'])
    ).order_by(MeasureAssignment.due_at.asc()).all()

# Add this to your notifications route:
# overdue_assignments = get_company_overdue_assignments(current_user.company.id)
# Then pass them to the template
'''
        
        print("💡 Quick fix code created")
        print("📋 Manual steps needed:")
        print("1. Add the overdue assignment query to your notifications route")
        print("2. Pass overdue assignments to the template")
        print("3. Ensure template displays them in the overdue section")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating quick fix: {e}")
        return False

if __name__ == '__main__':
    success = diagnose_gehring_overdue()
    
    if success:
        print(f"\n✅ Diagnosis complete - found overdue measures!")
        print(f"🔧 If notifications still don't show, run the setup script:")
        print(f"   python setup_overdue_notifications.py")
    else:
        print(f"\n⚠️  No overdue measures found or other issues detected")
        quick_fix_for_gehring()
        
    print(f"\n🌐 To test notifications, visit:")
    print(f"   http://localhost:5000/company/notifications")