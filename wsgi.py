import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv(".env")

# Import and create Flask app
from app import create_app

# Create the application instance
app = create_app()

# Ensure app is available for gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

