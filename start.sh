#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Set Flask app and environment
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Show environment info
echo "================================"
echo "Environment Configuration:"
echo "FLASK_APP: $FLASK_APP"
echo "FLASK_ENV: $FLASK_ENV"
echo "DATABASE_URL: ${DATABASE_URL:0:30}..." # Show first 30 chars only for security
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "================================"

# Run database migrations
echo "Running database migrations..."
python -m flask db upgrade
echo "✓ Migrations complete."

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
