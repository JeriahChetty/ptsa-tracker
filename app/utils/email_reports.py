"""Email report utilities for system-wide notifications"""
from datetime import datetime, timedelta
from flask import current_app, render_template_string
from flask_mail import Message as MailMessage
from app.extensions import db, mail
from app.models import (
    User, Company, MeasureAssignment, AssistanceRequest, SystemSettings
)


def get_admin_emails():
    """Get all admin user email addresses"""
    admin_users = User.query.filter_by(role='admin', is_active=True).all()
    return [admin.email for admin in admin_users]


def get_additional_report_emails():
    """Get additional email addresses for progress reports from settings"""
    settings = SystemSettings.get_settings()
    if not settings.progress_report_additional_emails:
        return []
    
    # Split by comma and strip whitespace
    emails = [email.strip() for email in settings.progress_report_additional_emails.split(',')]
    return [email for email in emails if email]  # Filter out empty strings


def generate_progress_report_html():
    """Generate HTML content for the progress report email"""
    now = datetime.utcnow()
    
    # Get all companies
    companies = Company.query.order_by(Company.name).all()
    
    # Calculate overall statistics
    total_assignments = MeasureAssignment.query.count()
    completed = MeasureAssignment.query.filter_by(status='Completed').count()
    in_progress = MeasureAssignment.query.filter_by(status='In Progress').count()
    not_started = MeasureAssignment.query.filter_by(status='Not Started').count()
    needs_assistance = MeasureAssignment.query.filter_by(status='Needs Assistance').count()
    
    overdue = MeasureAssignment.query.filter(
        MeasureAssignment.due_at.isnot(None),
        MeasureAssignment.due_at < now,
        MeasureAssignment.status != 'Completed'
    ).count()
    
    # Get recent assistance requests (last 7 days)
    week_ago = now - timedelta(days=7)
    recent_assistance = AssistanceRequest.query.filter(
        AssistanceRequest.created_at >= week_ago,
        AssistanceRequest.decision == 'open'
    ).count()
    
    # Company-level statistics
    company_stats = []
    for company in companies:
        assignments = MeasureAssignment.query.filter_by(company_id=company.id).all()
        if not assignments:
            continue
        
        company_completed = sum(1 for a in assignments if a.status == 'Completed')
        company_total = len(assignments)
        company_overdue = sum(
            1 for a in assignments 
            if a.due_at and a.due_at < now and a.status != 'Completed'
        )
        company_assistance = sum(1 for a in assignments if a.status == 'Needs Assistance')
        
        completion_rate = (company_completed / company_total * 100) if company_total > 0 else 0
        
        company_stats.append({
            'name': company.name,
            'total': company_total,
            'completed': company_completed,
            'in_progress': sum(1 for a in assignments if a.status == 'In Progress'),
            'not_started': sum(1 for a in assignments if a.status == 'Not Started'),
            'overdue': company_overdue,
            'needs_assistance': company_assistance,
            'completion_rate': completion_rate
        })
    
    # Sort by completion rate (lowest first - needs attention)
    company_stats.sort(key=lambda x: x['completion_rate'])
    
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                      gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; 
                     border-left: 4px solid #667eea; }
        .stat-card h3 { margin: 0 0 10px 0; font-size: 14px; color: #666; text-transform: uppercase; }
        .stat-card .number { font-size: 32px; font-weight: bold; color: #333; }
        .stat-card.warning { border-left-color: #f59e0b; }
        .stat-card.danger { border-left-color: #ef4444; }
        .stat-card.success { border-left-color: #10b981; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; background: white; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }
        th { background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }
        td { padding: 12px; border-bottom: 1px solid #e5e7eb; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #f9fafb; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; 
                 font-size: 12px; font-weight: 600; }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-danger { background: #fee2e2; color: #991b1b; }
        .badge-info { background: #dbeafe; color: #1e40af; }
        .footer { margin-top: 40px; padding: 20px; background: #f8f9fa; 
                  border-radius: 8px; text-align: center; color: #666; }
        .progress-bar { background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; }
        .progress-fill { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                        height: 100%; display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 12px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 PTSA Tracker Progress Report</h1>
            <p>Generated on {{ report_date }}</p>
        </div>
        
        <div class="section">
            <h2>Overall System Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Assignments</h3>
                    <div class="number">{{ total_assignments }}</div>
                </div>
                <div class="stat-card success">
                    <h3>Completed</h3>
                    <div class="number">{{ completed }}</div>
                </div>
                <div class="stat-card">
                    <h3>In Progress</h3>
                    <div class="number">{{ in_progress }}</div>
                </div>
                <div class="stat-card warning">
                    <h3>Not Started</h3>
                    <div class="number">{{ not_started }}</div>
                </div>
                <div class="stat-card danger">
                    <h3>Overdue</h3>
                    <div class="number">{{ overdue }}</div>
                </div>
                <div class="stat-card warning">
                    <h3>Need Assistance</h3>
                    <div class="number">{{ needs_assistance }}</div>
                </div>
            </div>
        </div>
        
        {% if recent_assistance > 0 %}
        <div class="section">
            <h2>⚠️ Recent Assistance Requests</h2>
            <p><strong>{{ recent_assistance }}</strong> open assistance request(s) in the last 7 days require your attention.</p>
        </div>
        {% endif %}
        
        <div class="section">
            <h2>Company Performance Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Total</th>
                        <th>Completed</th>
                        <th>In Progress</th>
                        <th>Overdue</th>
                        <th>Completion Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {% for company in company_stats %}
                    <tr>
                        <td><strong>{{ company.name }}</strong></td>
                        <td>{{ company.total }}</td>
                        <td>
                            <span class="badge badge-success">{{ company.completed }}</span>
                        </td>
                        <td>
                            <span class="badge badge-info">{{ company.in_progress }}</span>
                        </td>
                        <td>
                            {% if company.overdue > 0 %}
                            <span class="badge badge-danger">{{ company.overdue }}</span>
                            {% else %}
                            <span class="badge badge-success">0</span>
                            {% endif %}
                        </td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {{ company.completion_rate }}%">
                                    {{ "%.1f"|format(company.completion_rate) }}%
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>This is an automated progress report from PTSA Tracker.</p>
            <p>Log in to the system for detailed information and to take action.</p>
            <p><a href="{{ app_url }}" style="color: #667eea;">Access PTSA Tracker</a></p>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(
        html_template,
        report_date=now.strftime('%B %d, %Y at %H:%M UTC'),
        total_assignments=total_assignments,
        completed=completed,
        in_progress=in_progress,
        not_started=not_started,
        overdue=overdue,
        needs_assistance=needs_assistance,
        recent_assistance=recent_assistance,
        company_stats=company_stats,
        app_url=current_app.config.get('APP_URL', 'https://ptsa-tracker-du81.onrender.com')
    )


def send_progress_report():
    """Send progress report email to all admins and additional recipients"""
    if not mail:
        current_app.logger.warning("Mail not configured, cannot send progress report")
        return False
    
    settings = SystemSettings.get_settings()
    
    if not settings.progress_report_enabled:
        current_app.logger.info("Progress reports are disabled")
        return False
    
    # Get all recipients
    admin_emails = get_admin_emails()
    additional_emails = get_additional_report_emails()
    all_recipients = admin_emails + additional_emails
    
    if not all_recipients:
        current_app.logger.warning("No recipients for progress report")
        return False
    
    # Generate report content
    html_content = generate_progress_report_html()
    
    try:
        msg = MailMessage(
            subject=f"PTSA Tracker Progress Report - {datetime.utcnow().strftime('%B %d, %Y')}",
            recipients=all_recipients,
            html=html_content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ptsa-tracker.com')
        )
        
        mail.send(msg)
        
        # Update last sent timestamp
        settings.last_progress_report_sent = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Progress report sent to {len(all_recipients)} recipient(s)")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send progress report: {str(e)}")
        return False


def send_due_date_reminders():
    """Send reminder emails to companies about upcoming due dates"""
    if not mail:
        current_app.logger.warning("Mail not configured, cannot send reminders")
        return False
    
    settings = SystemSettings.get_settings()
    
    if not settings.reminder_email_enabled:
        current_app.logger.info("Reminder emails are disabled")
        return False
    
    # Calculate the target due date (X days from now)
    from datetime import datetime, timedelta
    target_date = datetime.utcnow() + timedelta(days=settings.reminder_days_before)
    target_date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    target_date_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Find assignments due on the target date that are not completed
    assignments = MeasureAssignment.query.filter(
        MeasureAssignment.due_at.isnot(None),
        MeasureAssignment.due_at >= target_date_start,
        MeasureAssignment.due_at <= target_date_end,
        MeasureAssignment.status != 'Completed'
    ).all()
    
    if not assignments:
        current_app.logger.info(f"No assignments due in {settings.reminder_days_before} days")
        return True
    
    # Group assignments by company
    company_assignments = {}
    for assignment in assignments:
        company_id = assignment.company_id
        if company_id not in company_assignments:
            company_assignments[company_id] = []
        company_assignments[company_id].append(assignment)
    
    emails_sent = 0
    
    # Send one email per company with all their upcoming assignments
    for company_id, assignments_list in company_assignments.items():
        company = Company.query.get(company_id)
        if not company:
            continue
        
        # Get company users
        company_users = User.query.filter_by(company_id=company_id, is_active=True).all()
        company_emails = [user.email for user in company_users]
        
        if not company_emails:
            current_app.logger.warning(f"No active users for company {company.name}")
            continue
        
        # Generate email content
        html_content = render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .alert { background: #fef3c7; border-left: 4px solid #f59e0b; 
                padding: 15px; border-radius: 4px; margin: 20px 0; }
        .measure-list { background: white; border-radius: 8px; overflow: hidden; 
                       box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .measure-item { padding: 15px; border-bottom: 1px solid #e5e7eb; }
        .measure-item:last-child { border-bottom: none; }
        .measure-name { font-weight: 600; color: #1f2937; margin-bottom: 5px; }
        .measure-due { color: #f59e0b; font-size: 14px; }
        .measure-status { display: inline-block; padding: 4px 12px; border-radius: 12px; 
                         font-size: 12px; font-weight: 600; }
        .status-not-started { background: #fee2e2; color: #991b1b; }
        .status-in-progress { background: #dbeafe; color: #1e40af; }
        .status-needs-assistance { background: #fef3c7; color: #92400e; }
        .button { display: inline-block; background: #f59e0b; color: white; 
                 padding: 12px 24px; text-decoration: none; border-radius: 6px; 
                 font-weight: 600; margin: 20px 0; }
        .footer { margin-top: 30px; padding: 20px; background: #f8f9fa; 
                 border-radius: 8px; text-align: center; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Upcoming Due Dates Reminder</h1>
            <p>{{ company_name }}</p>
        </div>
        
        <div class="alert">
            <strong>⚠️ Attention Required</strong><br>
            You have <strong>{{ assignment_count }}</strong> measure(s) due in <strong>{{ days_count }} days</strong> 
            ({{ due_date }}).
        </div>
        
        <div class="measure-list">
            {% for assignment in assignments %}
            <div class="measure-item">
                <div class="measure-name">{{ assignment.measure.name }}</div>
                <div class="measure-due">
                    Due: {{ assignment.due_at.strftime('%B %d, %Y') }}
                    <span class="measure-status status-{{ assignment.status.lower().replace(' ', '-') }}">
                        {{ assignment.status }}
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <a href="{{ dashboard_url }}" class="button">View Dashboard & Take Action</a>
        
        <div class="footer">
            <p><strong>This is an automated reminder from PTSA Tracker.</strong></p>
            <p>Please log in to update the status of your measures and ensure they are completed on time.</p>
            <p>If you've already completed these measures, please update their status in the system.</p>
        </div>
    </div>
</body>
</html>
        """,
            company_name=company.name,
            assignment_count=len(assignments_list),
            days_count=settings.reminder_days_before,
            due_date=target_date.strftime('%B %d, %Y'),
            assignments=assignments_list,
            dashboard_url=f"{current_app.config.get('APP_URL', 'https://ptsa-tracker-du81.onrender.com')}/company/dashboard"
        )
        
        try:
            msg = MailMessage(
                subject=f"⏰ Reminder: {len(assignments_list)} Measure(s) Due in {settings.reminder_days_before} Days",
                recipients=company_emails,
                html=html_content,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ptsa-tracker.com')
            )
            
            mail.send(msg)
            emails_sent += 1
            current_app.logger.info(f"Reminder sent to {company.name} ({len(company_emails)} recipients)")
            
        except Exception as e:
            current_app.logger.error(f"Failed to send reminder to {company.name}: {str(e)}")
    
    # Update last check timestamp
    settings.last_reminder_check = datetime.utcnow()
    db.session.commit()
    
    current_app.logger.info(f"Sent {emails_sent} reminder email(s) for {len(assignments)} assignment(s)")
    return emails_sent > 0


def send_assistance_notification(assistance_request):
    """Send email notification when a company requests assistance"""
    if not mail:
        current_app.logger.warning("Mail not configured, cannot send assistance notification")
        return False
    
    settings = SystemSettings.get_settings()
    
    if not settings.assistance_email_enabled:
        current_app.logger.info("Assistance email notifications are disabled")
        return False
    
    # Get admin emails
    admin_emails = get_admin_emails()
    
    if not admin_emails:
        current_app.logger.warning("No admin emails found for assistance notification")
        return False
    
    # Get assignment and company details
    assignment = assistance_request.assignment
    company = assignment.company if assignment else None
    measure = assignment.measure if assignment else None
    
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ef4444; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .alert-badge { display: inline-block; background: #fef3c7; color: #92400e; 
                      padding: 8px 16px; border-radius: 4px; font-weight: 600; margin: 10px 0; }
        .details { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .details h3 { margin-top: 0; color: #667eea; }
        .detail-row { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }
        .detail-row strong { color: #666; display: inline-block; min-width: 150px; }
        .notes { background: #fff3cd; padding: 15px; border-left: 4px solid #f59e0b; 
                border-radius: 4px; margin: 15px 0; }
        .button { display: inline-block; background: #667eea; color: white; 
                 padding: 12px 24px; text-decoration: none; border-radius: 6px; 
                 font-weight: 600; margin: 20px 0; }
        .footer { margin-top: 30px; padding: 20px; background: #f8f9fa; 
                 border-radius: 8px; text-align: center; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Assistance Request</h1>
            <div class="alert-badge">REQUIRES ATTENTION</div>
        </div>
        
        <p>A company has requested assistance with a measure assignment.</p>
        
        <div class="details">
            <h3>Request Details</h3>
            <div class="detail-row">
                <strong>Company:</strong> {{ company_name }}
            </div>
            <div class="detail-row">
                <strong>Measure:</strong> {{ measure_name }}
            </div>
            <div class="detail-row">
                <strong>Previous Status:</strong> {{ prev_status }}
            </div>
            <div class="detail-row">
                <strong>Requested By:</strong> {{ requested_by }}
            </div>
            <div class="detail-row">
                <strong>Requested On:</strong> {{ requested_at }}
            </div>
        </div>
        
        {% if notes %}
        <div class="notes">
            <strong>Additional Notes:</strong><br>
            {{ notes }}
        </div>
        {% endif %}
        
        <a href="{{ view_url }}" class="button">View Assignment Details</a>
        
        <div class="footer">
            <p>This is an automated notification from PTSA Tracker.</p>
            <p>Please log in to the system to review and respond to this assistance request.</p>
        </div>
    </div>
</body>
</html>
    """
    
    html_content = render_template_string(
        html_template,
        company_name=company.name if company else 'Unknown',
        measure_name=measure.name if measure else 'Unknown',
        prev_status=assistance_request.prev_status or 'Not Started',
        requested_by=assistance_request.requested_by.email if assistance_request.requested_by else 'Unknown',
        requested_at=(assistance_request.requested_at or assistance_request.created_at).strftime('%B %d, %Y at %H:%M UTC'),
        notes=assistance_request.decision_notes or '',
        view_url=f"{current_app.config.get('APP_URL', 'https://ptsa-tracker-du81.onrender.com')}/admin/assignment/{assignment.id}" if assignment else '#'
    )
    
    try:
        msg = MailMessage(
            subject=f"🚨 Assistance Request: {company.name if company else 'Company'} - {measure.name if measure else 'Measure'}",
            recipients=admin_emails,
            html=html_content,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ptsa-tracker.com')
        )
        
        mail.send(msg)
        current_app.logger.info(f"Assistance notification sent to {len(admin_emails)} admin(s)")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send assistance notification: {str(e)}")
        return False
