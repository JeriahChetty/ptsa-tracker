"""Health check endpoint for Azure App Service"""

from flask import Blueprint, jsonify
from app.extensions import db
from app.models import User, Company

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connectivity
        user_count = User.query.count()
        company_count = Company.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'users': user_count,
            'companies': company_count,
            'version': '2.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
