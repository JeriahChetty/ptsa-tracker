"""SendGrid HTTP API helper for sending emails"""
import os
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


def send_email_via_sendgrid(subject, recipients, html_content, sender=None):
    """
    Send email using SendGrid HTTP API instead of SMTP
    
    Args:
        subject: Email subject line
        recipients: List of recipient email addresses
        html_content: HTML content of the email
        sender: Sender email address (defaults to environment variable)
    """
    print(f"[SendGrid] Starting email send...", flush=True)
    print(f"[SendGrid] Recipients: {recipients}", flush=True)
    print(f"[SendGrid] Subject: {subject}", flush=True)
    
    # Get API key from environment
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print("[SendGrid] ERROR: API key not found!", flush=True)
        raise Exception("SENDGRID_API_KEY not configured in environment variables")
    
    print(f"[SendGrid] API key found: {api_key[:20]}...", flush=True)
    
    # Get sender email
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'info@ptsa.co.za')
    
    print(f"[SendGrid] Sender: {sender}", flush=True)
    
    try:
        # Ensure recipients is a list
        if isinstance(recipients, str):
            recipients = [recipients]
        
        # Create SendGrid message
        from_email = Email(sender)
        to_emails = [To(email) for email in recipients]
        content = Content("text/html", html_content)
        
        # Build message
        message = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=content
        )
        
        # Send via SendGrid API
        print("[SendGrid] Creating API client...", flush=True)
        sg = SendGridAPIClient(api_key)
        print("[SendGrid] Sending message via API...", flush=True)
        response = sg.send(message)
        
        # Log response
        print(f"[SendGrid] API response status: {response.status_code}", flush=True)
        print(f"[SendGrid] Email sent to {len(recipients)} recipient(s): {', '.join(recipients)}", flush=True)
        current_app.logger.info(f"SendGrid API response: {response.status_code}")
        current_app.logger.info(f"Email sent to {len(recipients)} recipient(s): {', '.join(recipients)}")
        
        return True
        
    except Exception as e:
        print(f"[SendGrid] ERROR: {str(e)}", flush=True)
        current_app.logger.error(f"SendGrid API error: {str(e)}")
        raise
