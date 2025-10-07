#!/bin/bash
set -e

echo "🚀 Starting PTSA Tracker deployment..."

# Debug environment
echo "🔍 Environment check:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   PORT: ${PORT:-10000}"
echo "   Working directory: $(pwd)"
echo "   Current user: $(whoami)"
echo "   User ID: $(id)"
echo "   Python version: $(python --version)"

# List files to ensure everything is there
echo "📁 Files in /app:"
ls -la /app/

# Test if wsgi module can be imported
echo "🧪 Testing wsgi import..."
python -c "import wsgi; print('✅ WSGI import successful')"

# Ensure database directory exists with proper permissions
echo "📁 Setting up database directory..."
mkdir -p /app/instance
chmod 755 /app/instance
echo "   Directory permissions:"
ls -la /app/ | grep instance
echo "   Directory contents:"
ls -la /app/instance/ || echo "   (directory is empty)"

# Initialize database
echo "📋 Initializing database..."
python init_db.py

echo "✅ Database initialization complete"

# Start Gunicorn with explicit module path
echo "🌐 Starting web server..."
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --worker-class sync --timeout 120 --log-level debug wsgi:app
