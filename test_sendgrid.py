"""Test SendGrid SMTP connection"""
import smtplib
from email.message import EmailMessage

# SendGrid SMTP settings
MAIL_SERVER = "smtp.sendgrid.net"
MAIL_PORT = 587
MAIL_USERNAME = "apikey"
MAIL_PASSWORD = "SG.8b0Gcd433iMcaQOMr2yMnA.fAfLrHIUPZvNKpYdBYfKu6Zzp_A0HFuP0n+X2DlnqfoG"  # Replace with your actual key
MAIL_FROM = "info@ptsa.co.za"
MAIL_TO = "info@ptsa.co.za"

print("🔌 Testing SendGrid SMTP connection...")
print(f"Server: {MAIL_SERVER}:{MAIL_PORT}")
print(f"Username: {MAIL_USERNAME}")
print(f"From: {MAIL_FROM}")
print(f"To: {MAIL_TO}")
print()

try:
    # Create message
    msg = EmailMessage()
    msg['Subject'] = 'Test Email from PTSA Tracker'
    msg['From'] = MAIL_FROM
    msg['To'] = MAIL_TO
    msg.set_content('This is a test email sent via SendGrid SMTP.')
    
    # Connect and send
    print("📡 Connecting to SMTP server...")
    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=30) as server:
        print("🔐 Starting TLS...")
        server.starttls()
        
        print("🔑 Logging in...")
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        
        print("📧 Sending email...")
        server.send_message(msg)
        
    print("✅ SUCCESS! Email sent successfully!")
    print("Check your inbox at info@ptsa.co.za")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())
