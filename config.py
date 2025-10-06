from datetime import timedelta
import os

# Production configuration for Azure
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-32+chars')

# Database configuration - prioritize Azure DATABASE_URL
if os.environ.get('DATABASE_URL'):
    # Azure PostgreSQL connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
elif os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING'):
    # Alternative Azure connection string format
    SQLALCHEMY_DATABASE_URI = os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING')
else:
    # Local development fallback
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'ptsa.db')}"

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'pool_size': 10,
    'max_overflow': 20
}

# Email configuration from environment
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'mail.ptsa.co.za')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'info@ptsa.co.za')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'wqMvrJm4VZp')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'ED Tracker <info@ptsa.co.za>')

class Config:
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TYPE = 'filesystem'
    
    # Upload settings for Azure
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Azure specific settings
    AZURE_STORAGE_ACCOUNT = os.environ.get('AZURE_STORAGE_ACCOUNT')
    AZURE_STORAGE_KEY = os.environ.get('AZURE_STORAGE_KEY')
    AZURE_STORAGE_CONTAINER = os.environ.get('AZURE_STORAGE_CONTAINER', 'uploads')
