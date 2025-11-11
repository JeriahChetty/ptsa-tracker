"""SendGrid HTTP API helper for sending emails"""
import os
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


def send_email_via_sendgrid(subject, recipients, html_content, sender=None):
    """
    Send email using SendGrid HTTP API (bypasses SMTP firewall issues)
    
    Args:
        subject: Email subject line
        recipients: List of recipient email addresses
        html_content: HTML email content
        sender: From email address (defaults to MAIL_DEFAULT_SENDER)
    
    Returns:
        bool: True if successful, raises exception otherwise
    """
    try:
        # Get SendGrid API key from environment
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            raise Exception("SENDGRID_API_KEY not configured in environment variables")
        
        # Use default sender if not provided
        if not sender:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'info@ptsa.co.za')
        
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
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Log response
        current_app.logger.info(f"SendGrid API response: {response.status_code}")
        current_app.logger.info(f"Email sent to {len(recipients)} recipient(s): {', '.join(recipients)}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"SendGrid API error: {str(e)}")
        raise
