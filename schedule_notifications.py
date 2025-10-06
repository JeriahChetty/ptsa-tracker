import os
import sys
import traceback
import logging
from flask.cli import FlaskGroup

# Set up logging
logging.basicConfig(
    filename='notification_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the Flask notify-due command to send deadline notifications."""
    try:
        from app import create_app
        app = create_app()
        cli = FlaskGroup(create_app=lambda: app)
        sys.argv = ['flask', 'notify-due']
        cli()
        print("Notification process completed successfully")
    except Exception as e:
        error_msg = f"Notification error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        logging.error(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    main()
