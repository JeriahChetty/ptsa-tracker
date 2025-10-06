# app/routes/__init__.py

from .admin_routes import admin_bp
from .company_routes import company_bp
from .auth_routes import auth_bp

def register_blueprints(app):
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(auth_bp)