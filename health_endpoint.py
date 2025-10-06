# Add health check endpoint to app.py
# This should be added to your main Flask application file

from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Azure App Service"""
    return {
        'status': 'healthy',
        'service': 'ptsa-tracker',
        'timestamp': datetime.utcnow().isoformat()
    }, 200