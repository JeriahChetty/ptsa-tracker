#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for Tesseract OCR
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
