#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
# We use 'flask db upgrade' which is the standard command for applying migrations.
# This ensures the database schema is up-to-date before the app starts.
echo "Running database migrations..."
flask db upgrade
echo "Migrations complete."

# Start the Gunicorn server
# This is the same command that was in render.yaml
# It will only run if the migrations above succeed.
echo "Starting Gunicorn server..."
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
