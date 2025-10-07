#!/bin/bash
set -e

echo "🚀 Starting PTSA Tracker deployment..."

# Initialize database
echo "📋 Initializing database..."
python init_db.py

echo "✅ Database initialization complete"

# Start Gunicorn
echo "🌐 Starting web server..."
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --worker-class sync --timeout 120 --log-level info wsgi:app
