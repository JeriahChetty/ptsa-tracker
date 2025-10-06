from app import create_app
from app.extensions import db

def main():
    """Set up or update notification configuration."""
    app = create_app()
    with app.app_context():
        from app.models import NotificationConfig
        # Find or create the notification config
        config = NotificationConfig.query.get(1)
        if not config:
            config = NotificationConfig(id=1)
            db.session.add(config)
        
        # Configure settings (adjust as needed)
        config.lead_days = 7       # Send notifications 7 days before deadline
        config.send_hour_utc = 7    # Send at 7:00 UTC
        config.send_minute_utc = 0  # (7:00 AM UTC)
        
        db.session.commit()
        print(f"Notification config set: {config.lead_days} days before deadline at {config.send_hour_utc:02d}:{config.send_minute_utc:02d} UTC")

if __name__ == '__main__':
    main()
