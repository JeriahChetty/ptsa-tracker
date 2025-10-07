#!/bin/bash
set -e

echo "🚀 Starting PTSA Tracker deployment..."

# Debug environment
echo "🔍 Environment check:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   PORT: ${PORT:-10000}"
echo "   Working directory: $(pwd)"
echo "   Python version: $(python --version)"

# List files to ensure everything is there
echo "📁 Files in /app:"
ls -la /app/

# Test if wsgi module can be imported
echo "🧪 Testing wsgi import..."
python -c "import wsgi; print('✅ WSGI import successful')"

# Initialize database
echo "📋 Initializing database..."
python init_db.py

echo "✅ Database initialization complete"

# Start Gunicorn with explicit module path
echo "🌐 Starting web server..."
exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --worker-class sync --timeout 120 --log-level debug wsgi:app
