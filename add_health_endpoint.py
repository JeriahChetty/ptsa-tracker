#!/usr/bin/env python3
"""
Add health check endpoint to PTSA Tracker Flask app
"""

def add_health_endpoint():
    """Add health check endpoint to the Flask app"""
    
    routes_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes.py"
    
    health_endpoint_code = '''
@app.route('/health')
def health_check():
    """Health check endpoint for container monitoring"""
    try:
        # Basic health checks
        from datetime import datetime
        from app.extensions import db
        
        # Check database connection
        db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ptsa-tracker',
            'version': '1.0.0'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503
'''
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if health endpoint already exists
        if '/health' in content:
            print("✅ Health endpoint already exists")
            return True
        
        # Add the health endpoint at the end of the file
        content += health_endpoint_code
        
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Health endpoint added to routes.py")
        return True
        
    except Exception as e:
        print(f"❌ Error adding health endpoint: {e}")
        return False

if __name__ == '__main__':
    print("🏥 Adding health check endpoint...")
    add_health_endpoint()
    print("✅ Health endpoint ready for Docker deployment")