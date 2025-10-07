#!/bin/bash

# Azure Web App startup script for PTSA Tracker
echo "Starting PTSA Tracker application..."

# Wait for database to be ready (if using Azure Database)
echo "Checking database connectivity..."
python -c "
try:
    from app import create_app
    from app.extensions import db
    app = create_app()
    with app.app_context():
        db.engine.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    # Don't exit as we might be using SQLite
"

# Run database migrations/setup
echo "Setting up database..."
python deploy_db.py

# Start the application with Gunicorn
echo "Starting web server..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} \
              --workers 2 \
              --worker-class sync \
              --worker-connections 1000 \
              --max-requests 1000 \
              --max-requests-jitter 100 \
              --timeout 120 \
              --keepalive 5 \
              --log-level info \
              --access-logfile - \
              --error-logfile - \
              app:create_app\(\)