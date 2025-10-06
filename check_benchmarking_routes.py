#!/usr/bin/env python3
"""
Quick route fix - identify and fix benchmarking routes
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_benchmarking_routes():
    """Check for benchmarking-related routes"""
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print("🔍 Searching for benchmarking routes...")
            
            benchmarking_routes = []
            company_routes = []
            
            for rule in app.url_map.iter_rules():
                rule_str = str(rule).lower()
                endpoint = rule.endpoint.lower()
                methods = list(rule.methods - {'HEAD', 'OPTIONS'})
                
                # Check for benchmarking related routes
                if 'benchmark' in rule_str or 'benchmark' in endpoint:
                    benchmarking_routes.append({
                        'endpoint': rule.endpoint,
                        'path': str(rule),
                        'methods': methods
                    })
                
                # Check for company related routes that might handle benchmarking
                if 'companies' in rule_str and rule.endpoint.startswith('admin'):
                    company_routes.append({
                        'endpoint': rule.endpoint,
                        'path': str(rule),
                        'methods': methods
                    })
            
            print("\n📊 BENCHMARKING ROUTES:")
            if benchmarking_routes:
                for route in benchmarking_routes:
                    print(f"  ✅ {route['endpoint']} ({', '.join(route['methods'])}) - {route['path']}")
            else:
                print("  ❌ No dedicated benchmarking routes found")
            
            print("\n🏢 COMPANY ROUTES (might handle benchmarking):")
            for route in sorted(company_routes, key=lambda x: x['endpoint']):
                print(f"  📝 {route['endpoint']} ({', '.join(route['methods'])}) - {route['path']}")
                
            return benchmarking_routes, company_routes
            
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        return [], []

if __name__ == '__main__':
    check_benchmarking_routes()