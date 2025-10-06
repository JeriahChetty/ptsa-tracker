from app import create_app
from app.routes.admin_routes import _send_bulk_email
import sys
import traceback

def main():
    """Test email sending functionality."""
    try:
        app = create_app()
        with app.app_context():
            recipient = input("Enter test recipient email: ")
            subject = "PTSA Tracker Email Test"
            body = "This is a test email from your PTSA Tracker application."
            
            print("Sending test email...")
            sent = _send_bulk_email(app, [(recipient, subject, body)])
            
            if sent == 1:
                print(f"Email sent successfully to {recipient}")
            else:
                print(f"Failed to send email. Check your SMTP configuration in instance/config.py")
                print("Make sure you have set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD, etc.")
    except Exception as e:
        print(f"Error testing email: {str(e)}")
        print(traceback.format_exc())
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
