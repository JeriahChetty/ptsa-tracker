# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# Where to send unauthenticated users
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

# Mail is optional; we don't require flask_mail at import time
try:
    from flask_mail import Mail  # type: ignore
    mail = Mail()
except Exception:
    mail = None  # not installed / not used
