#!/usr/bin/env python3
"""
WSGI entry point for PTSA Tracker
"""
import os

# Set environment to production
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask application factory
from app import create_app

# Create the Flask application instance
app = create_app('production')

# Make sure the app is available for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

