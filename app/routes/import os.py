import os

SECRET_KEY = 'your-secure-production-key'  # Generate a strong random key

# Database - for production consider PostgreSQL or MySQL
SQLALCHEMY_DATABASE_URI = 'sqlite:///ptsa_prod.db'  # Or other production database

# Email configuration
MAIL_SERVER = 'smtp.yourdomain.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'notifications@yourdomain.com'
MAIL_PASSWORD = 'your-mail-password'
MAIL_DEFAULT_SENDER = 'PTSA Tracker <notifications@yourdomain.com>'

# Upload folder - make sure this directory exists and is writable
UPLOAD_FOLDER = '/home/ptsa/ptsa_tracker/uploads'

# Production settings
DEBUG = False
TESTING = False
