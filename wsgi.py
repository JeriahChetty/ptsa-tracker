#!/usr/bin/env python3
"""
WSGI entry point for PTSA Tracker application
"""
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Flask application factory
from app import create_app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # For local development
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

